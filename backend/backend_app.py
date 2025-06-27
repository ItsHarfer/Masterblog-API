import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint

from config.loader import load_config

app = Flask(__name__)
CORS(app)

# Loading constants
config = load_config()

# Configure SwaggerUI
swagger_cfg = config["swagger"]
swagger_ui_blueprint = get_swaggerui_blueprint(
    swagger_cfg["url"], swagger_cfg["api_url"], config=swagger_cfg["config"]
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=swagger_cfg["url"])

# Configure Rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"],
)

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def fetch_data_from_json() -> list:
    """
    Fetches and returns data from a JSON file.

    :return: The content of the JSON file as a Python data structure.
    :rtype: list
    """
    path = Path(__file__).parent / "data" / "posts.json"

    if not path.exists():
        logging.warning(f"Data file does not exist at {path}. Returning empty list.")
        return []

    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
        logging.error(f"Failed to decode JSON from {path}: {e}")
    except (OSError, IOError) as e:
        logging.error(f"File access error while reading {path}: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error while reading JSON from {path}: {e}")
    return []


def save_data_to_json(data):
    """
    Save the list of data to the JSON file.

    :param data: List of data to save.
    """
    path = Path(__file__).parent / "data" / "posts.json"

    if not path.exists():
        logging.warning(f"Data file does not exist at {path}. Returning empty list.")
        return []

    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
    except (OSError, IOError) as e:
        logging.error(f"Failed to write JSON to {path}: {e}")
    except TypeError as e:
        logging.error(f"Data serialization failed while writing to {path}: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error while writing JSON to {path}: {e}")


def parse_post_field_input():
    """
    Extract and trim 'title', 'content', 'author', and 'date' fields from a JSON request body or query parameters.

    Priority:
    - JSON body fields ('title', 'content', 'author', 'date') are checked first.
    - If not present, fallback to query parameters.

    :return: Tuple of (title, content, author, date), each either a trimmed string or None
    :raises: None
    """

    # Safely attempt to parse JSON body without raising an error on failure
    json_data = request.get_json(silent=True) or {}
    args = request.args

    raw_title = json_data.get("title") or args.get("title")
    raw_content = json_data.get("content") or args.get("content")
    raw_author = json_data.get("author") or args.get("author")
    raw_date = json_data.get("date") or args.get("date")

    title = raw_title.strip() if isinstance(raw_title, str) else None
    content = raw_content.strip() if isinstance(raw_content, str) else None
    author = raw_author.strip() if isinstance(raw_author, str) else None
    date = raw_date.strip() if isinstance(raw_date, str) else None

    return title, content, author, date


def parse_sort_query_input():
    """
    Extract and trim 'sort' and 'direction' query parameters.

    :return: Tuple of (sort, direction), each either a trimmed string or None
    :raises: None
    """
    args = request.args

    raw_sort = args.get("sort")
    raw_direction = args.get("direction")

    sort = raw_sort.strip() if isinstance(raw_sort, str) else None
    direction = raw_direction.strip() if isinstance(raw_direction, str) else None

    return sort, direction


def get_field_error_response(title, content, author, date):
    """
    Generate and return an error response for missing or empty fields.

    :param date: The date field to validate
    :param author: The author field to validate
    :param title: The title field to validate
    :param content: The content field to validate
    :return: Aborts with a 400 response including a descriptive error message
    :raises: 400: If either or both fields are missing or empty.
    """
    missing_fields = []
    if not title:
        missing_fields.append("title")
    if not content:
        missing_fields.append("content")
    if not author:
        missing_fields.append("author")
    if not date:
        missing_fields.append("date")

    if missing_fields:
        abort(400, description=f"Missing required fields: {', '.join(missing_fields)}")


def get_post_by_id(post_id):
    """
    Find and return the post by ID.

    :param post_id: The ID of the post to find
    :return: The post object if found.
    :raises: 404: If no post with the given ID exists.
    """
    post = next((post for post in posts if post["id"] == post_id), None)
    if not post:
        return abort(404, description=f"Post with id {post_id} not found.")
    return post


def validate_post_id(post_id):
    """
    Validate that the post ID is an integer.

    :param post_id: The post ID to validate
    :return: The integer ID if valid.
    :raises: 400: If post_id is not an integer.
    """
    try:
        post_id = int(post_id)
    except ValueError:
        abort(400, description="Post ID must be an integer")
    return post_id


@app.errorhandler(400)
def bad_request(error):
    """
    Handle 400 Bad Request errors and return a JSON response.

    :param error: The error object raised by Flask
    :return: A JSON response with a message and error details, HTTP 400 status code
    """
    return (
        jsonify(
            {
                "message": "Bad Request",
                "error": (
                    error.description if hasattr(error, "description") else str(error)
                ),
            }
        ),
        400,
    )


@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Handle 429 Too Many Requests errors and return a JSON response.

    :param e: The rate limit exception raised by Flask-Limiter
    :return: A JSON response with an error message and HTTP 429 status code
    """
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429


@app.route("/api/posts", methods=["GET", "POST"])
@limiter.limit("10/minute")
def handle_posts():
    """
    Handle GET and POST requests to retrieve or create blog posts.

    :return: JSON list of posts (GET) or newly created post with ID (POST)
    :raises:
        400: If title or content is missing in a POST request.
        429: If rate limit exceeded.
    """

    if request.method == "POST":
        title, content, author, date = parse_post_field_input()
        if title and content and author and date:
            new_id = max((post["id"] for post in posts), default=0) + 1
            new_post = {
                "id": new_id,
                "title": title,
                "content": content,
                "author": author,
                "date": date,
            }
            posts.append(new_post)
            save_data_to_json(posts)
            return (
                jsonify({"message": "Post created successfully", "post": new_post}),
                201,
            )
        return get_field_error_response(title, content, author, date)

    # GET request
    sort, direction = parse_sort_query_input()

    if sort:
        if sort not in ("title", "content", "author", "date"):
            abort(400, description=f"Invalid sort field: {sort}")

        if direction not in ("asc", "desc"):
            abort(400, description=f"Invalid sort direction: {direction}")

        try:
            reverse = direction == "desc"

            if sort == "date":
                posts.sort(
                    key=lambda post: datetime.strptime(
                        # Default date if a field is missing or None
                        post.get("date", "1970-01-01"),
                        "%Y-%m-%d",
                    ),
                    reverse=reverse,
                )
            else:
                posts.sort(
                    key=lambda post: (str(post.get(sort) or "")).lower(),
                    reverse=reverse,
                )

        except (KeyError, ValueError, TypeError) as e:
            abort(400, description=f"Error during sorting: {str(e)}")

    return jsonify(posts), 200


@app.route("/api/posts/<post_id>", methods=["DELETE"])
@limiter.limit("10/minute")
def delete_post(post_id: str):
    """
    Delete a blog post by ID.

    :param post_id: The ID of the post to delete
    :return: JSON message on success, aborts with 400 or 404 on failure
    :raises:
        400: If post_id is invalid.
        404: If no post with the given ID exists.
        429: If rate limit exceeded.
    """
    post_id_int = validate_post_id(post_id)
    post = get_post_by_id(post_id_int)
    posts.remove(post)
    save_data_to_json(posts)
    return (
        jsonify({"message": f"Post {post_id_int} has been deleted successfully."}),
        200,
    )


@app.route("/api/posts/<post_id>", methods=["PUT"])
@limiter.limit("10/minute")
def update_post(post_id: str):
    """
    Update a blog post by ID

    :param post_id: The ID of the post to update
    :return: JSON message with updated post or error if not found/invalid
    :raises:
        400: If post_id is invalid or if neither field is provided.
        404: If no post with the given ID exists.
        429: If rate limit exceeded.
    """
    post_id_int = validate_post_id(post_id)
    title, content, author, date = parse_post_field_input()

    if not title and not content and not author and not date:
        abort(400, description="At least one field is required")

    post = get_post_by_id(post_id_int)

    if title:
        post["title"] = title
    if content:
        post["content"] = content
    if author:
        post["author"] = author
    if date:
        post["date"] = date

    return jsonify({"message": "Post updated successfully", "post": post}), 200


@app.route("/api/posts/search")
@limiter.limit("20/minute")
def search_post():
    """
    Search for blog posts by title or content.

    :return: JSON list of posts that match the given search terms.
    :raises:
        None explicitly, but may return empty list if no matches are found.
        Ensures no TypeError occurs by validating inputs before filtering.
        429: If rate limit is exceeded.
    """
    title, content, author, date = parse_post_field_input()

    filtered_posts = [
        post
        for post in posts
        if (title and title in post["title"])
        or (content and content in post["content"])
        or (author and author in post["author"])
        or (date and date in post["date"])
    ]

    if not filtered_posts:
        return jsonify([])

    save_data_to_json(filtered_posts)

    return jsonify(filtered_posts), 200


if __name__ == "__main__":
    posts = fetch_data_from_json()
    app.run(host="0.0.0.0", port=5002, debug=True)
