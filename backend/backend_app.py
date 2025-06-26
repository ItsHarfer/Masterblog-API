from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]


def validate_post_form_data():
    """
    Validates input JSON data from a POST request to extract and process the `title`
    and `content` fields. Ensures that both fields are properly trimmed and checks
    if they are provided and non-empty. Returns a tuple of `title` and `content`.

    :raises:
        Does not raise any exceptions itself but depends on caller handling any
        possible errors (e.g., issues parsing JSON from `request.get_json()`).

    :returns:
        A tuple containing the extracted and trimmed `title` and `content` if both
        are valid. If either the `title` or `content` is missing or empty, it
        returns a tuple with both elements as `None`.
    """
    data = request.get_json() or {}

    raw_title = data.get("title")
    raw_content = data.get("content")

    title = raw_title.strip() if isinstance(raw_title, str) else None
    content = raw_content.strip() if isinstance(raw_content, str) else None

    return title, content


def get_field_error_response(title, content):
    """
    Generates an HTTP response for field validation errors based on the provided
    title and content. The response contains an error message specifying the
    missing or invalid fields and assigns a 400 HTTP status code. This function
    is primarily used to ensure proper error communication when required input
    fields are either missing or empty.

    :param title: The title field to be validated.
    :type title: str
    :param content: The content field to be validated.
    :type content: str
    :return: A tuple containing a JSON response with an error message and
        the HTTP status code 400.
    :rtype: Tuple[flask.Response, int]
    """
    if not title and not content:
        abort(400, description="Title and content are required")
    elif not title:
        abort(400, description="Title is required")
    elif not content:
        abort(400, description="Content is required")


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


@app.route("/api/posts", methods=["GET", "POST"])
def handle_posts():
    """
    Handles GET and POST requests to manage blog posts.

    - GET: Returns a list of all stored posts.
    - POST: Validates title and content fields, generates a unique integer ID,
            stores the new post in memory, and returns it in the response.

    Returns:
        - 200 OK with post list (GET)
        - 201 Created with new post object (POST)
        - 400 Bad Request with descriptive error if fields are missing or invalid
    """
    if request.method == "POST":
        title, content = validate_post_form_data()
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
def delete_post(post_id: str):
    """
    Handles DELETE requests to delete a blog post by its ID.

    - Converts the provided `post_id` to an integer.
    - Validates that the ID is present and an integer.
    - Searches for a matching post in the in-memory list.
    - If found, deletes the post and returns a confirmation message.
    - If not found, returns a 404 Not Found error.
    - If ID is invalid or missing, returns a 400 Bad Request error.

    Parameters:
        post_id (str): The ID of the post to delete, passed as a URL parameter.

    Returns:
        - 200 OK with deletion confirmation if the post was found and removed.
        - 400 Bad Request if `post_id` is not an integer.
        - 404 Not Found if no post with the given ID exists.
    Edge cases:
        - post_id is always provided by Flask when the route is matched.
          If it were missing, the route itself would not be invoked.
    """
    try:
        post_id = int(post_id)
    except ValueError:
        abort(400, description="Post ID must be an integer")

    # Find the post by ID
    post = next((p for p in POSTS if p["id"] == post_id), None)
    if post:
        POSTS.remove(post)
        return (
            jsonify({"message": f"Post {post_id} has been deleted successfully."}),
            200,
        )

    return abort(404, description=f"Post with id {post_id} not found.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
