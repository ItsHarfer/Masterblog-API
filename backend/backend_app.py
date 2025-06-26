from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

limiter = Limiter(
    get_remote_address,  # basiert auf IP-Adresse
    app=app,  # deine Flask-App
    default_limits=["100 per hour"],  # globales Limit (optional)
)

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]


def parse_post_data():
    """
    Extract and trim the 'title' and 'content' fields from a JSON request body.

    :return: Tuple of (title, content), each either a trimmed string or None
    :raises: None
    """
    data = request.get_json() or {}

    raw_title = data.get("title")
    raw_content = data.get("content")

    title = raw_title.strip() if isinstance(raw_title, str) else None
    content = raw_content.strip() if isinstance(raw_content, str) else None

    return title, content


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
    post = next((post for post in POSTS if post["id"] == post_id), None)
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
        title, content = parse_post_data()
        if title and content:
            new_id = max((post["id"] for post in POSTS), default=0) + 1
            new_post = {"id": new_id, "title": title, "content": content}
            POSTS.append(new_post)
            return (
                jsonify({"message": "Post created successfully", "post": new_post}),
                201,
            )
        return get_field_error_response(title, content)

    # GET request
    return jsonify(POSTS)


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
    POSTS.remove(post)
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
    title, content = parse_post_data()

    if not title and not content:
        abort(400, description="At least one field is required")

    post = get_post_by_id(post_id_int)

    if title:
        post["title"] = title
    if content:
        post["content"] = content

    return jsonify({"message": "Post updated successfully", "post": post})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
