import json
import logging

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


def fetch_data_from_json():
    """
    Fetches and returns data from a JSON file.

    :return: The content of the JSON file as a Python data structure.
    :rtype: dict or list
    """
    with open("data/posts.json", "r") as f:
        return json.load(f)


def save_data_to_json(data):
    """
    Save the list of data to the JSON file.

    :param data: List of data to save.
    """
    with open("data/posts.json", "w") as f:
        json.dump(data, f)


def parse_post_field_input():
    """
    Extract and trim 'title' and 'content' fields from a JSON request body or query parameters.

    Priority:
    - JSON body fields ('title', 'content') are checked first.
    - If not present, fallback to query parameters.

    :return: Tuple of (title, content), each either a trimmed string or None
    :raises: None
    """

    # Safely attempt to parse JSON body without raising an error on failure
    json_data = request.get_json(silent=True) or {}
    args = request.args

    raw_title = json_data.get("title") or args.get("title")
    raw_content = json_data.get("content") or args.get("content")

    title = raw_title.strip() if isinstance(raw_title, str) else None
    content = raw_content.strip() if isinstance(raw_content, str) else None

    return title, content


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


def get_field_error_response(title, content):
    """
    Generate and return an error response for missing or empty fields.

    :param title: The title field to validate
    :param content: The content field to validate
    :return: Aborts with a 400 response including a descriptive error message
    :raises: 400: If either or both fields are missing or empty.
    """
    if not title and not content:
        abort(400, description="Title and content are required")
    elif not title:
        abort(400, description="Title is required")
    elif not content:
        abort(400, description="Content is required")


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
        title, content = parse_post_field_input()
        if title and content:
            new_id = max((post["id"] for post in posts), default=0) + 1
            new_post = {"id": new_id, "title": title, "content": content}
            posts.append(new_post)
            save_data_to_json(posts)
            return (
                jsonify({"message": "Post created successfully", "post": new_post}),
                201,
            )
        return get_field_error_response(title, content)

    # GET request
    sort, direction = parse_sort_query_input()

    if sort:
        if sort not in ("title", "content"):
            abort(400, description=f"Invalid sort field: {sort}")

        if direction not in ("asc", "desc"):
            abort(400, description=f"Invalid sort direction: {direction}")

        try:
            posts.sort(key=lambda post: post[sort], reverse=(direction == "desc"))
        except KeyError:
            abort(400, description=f"Sort key '{sort}' not found in one or more posts.")

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
    title, content = parse_post_field_input()

    if not title and not content:
        abort(400, description="At least one field is required")

    post = get_post_by_id(post_id_int)

    if title:
        post["title"] = title
    if content:
        post["content"] = content

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
    title, content = parse_post_field_input()

    filtered_posts = [
        post
        for post in posts
        if (title and title in post["title"])
        or (content and content in post["content"])
    ]

    if not filtered_posts:
        return jsonify([])

    save_data_to_json(filtered_posts)

    return jsonify(filtered_posts), 200


if __name__ == "__main__":
    posts = fetch_data_from_json()
    app.run(host="0.0.0.0", port=5002, debug=True)
