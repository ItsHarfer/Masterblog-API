"""
backend_app.py

Backend API module for the Masterblog API.

This script defines the RESTful backend logic for managing blog posts in the Masterblog system.
It supports creating, retrieving, updating, deleting, liking, and commenting on blog posts.
Posts are stored as structured JSON data in a local file (`data/posts.json`).

Features:
- REST API for blog post lifecycle management (CRUD operations)
- Support for liking and commenting on posts
- Sorting and searching functionality
- JSON-backed persistent data layer
- Swagger UI for API documentation
- Rate limiting using Flask-Limiter
- Cross-origin request support via Flask-CORS

Functions:
- `fetch_data_from_json()` and `save_data_to_json()` handle file I/O
- `get_post_by_id()` and `validate_post_id()` assist post access and validation
- Route handlers cover /api/posts endpoints for managing blog data

Required modules:
- Flask: Web framework for route handling
- Flask-Limiter: Rate-limiting functionality
- Flask-CORS: CORS support for cross-origin requests
- Flask-Swagger-UI: Documentation generation for the API
- json, logging, pathlib, datetime: for I/O, logging, path, and date handling

Author: Martin Haferanke
Date: 2025-06-30
"""

from datetime import datetime

from flask import jsonify, request, abort

from utils.json_io import fetch_data_from_json, save_data_to_json
from utils.parsers import parse_post_field_input, parse_sort_query_input
from utils.validators import get_field_error_response, validate_post_id
from utils.validators import validate_date_string
from utils.helpers import get_post_by_id

# App Config
from app_factory import create_app

app, limiter, config = create_app()


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

    # load existing posts
    posts = fetch_data_from_json()

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
                "likes": 0,
                "comments": [],
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

            # Explicitly validate and parse each post's date
            for post in posts:
                post["_parsed_date"] = validate_date_string(
                    post.get("date"), post.get("id")
                )

            # Sort by the parsed datetime objects
            posts.sort(
                key=lambda p: p["_parsed_date"],
                reverse=reverse,
            )

            # Clean up temporary parsed date field
            for post in posts:
                del post["_parsed_date"]

            # Skip the generic sort for non-date fields
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
    post = get_post_by_id(post_id_int, posts)
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

    post = get_post_by_id(post_id_int, posts)

    if title:
        post["title"] = title
    if content:
        post["content"] = content
    if author:
        post["author"] = author
    if date:
        post["date"] = date

    save_data_to_json(posts)

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

    return jsonify(filtered_posts), 200


# New route for liking a post
@app.route("/api/posts/<post_id>/like", methods=["POST"])
@limiter.limit("10/minute")
def like_post(post_id: str):
    """
    Increment the like count for a blog post by ID.

    :param post_id: The ID of the post to like
    :return: JSON message with updated post or error if not found
    :raises:
        400: If post_id is invalid.
        404: If no post with the given ID exists.
        429: If rate limit exceeded.
    """
    post_id_int = validate_post_id(post_id)
    post = get_post_by_id(post_id_int, posts)

    if "likes" not in post:
        post["likes"] = 0
    post["likes"] += 1

    save_data_to_json(posts)
    return jsonify({"message": "Post liked successfully", "post": post}), 200


@app.route("/api/posts/<post_id>/comment", methods=["POST"])
@limiter.limit("10/minute")
def comment_post(post_id: str):
    """
    Add a comment to a blog post by ID.

    :param post_id: The ID of the post to comment on.
    :type post_id: str
    :return: JSON message with updated post or error if comment is empty.
    :rtype: Response
    :raises 400: If comment is empty or post_id is invalid.
    :raises 404: If no post with the given ID exists.
    :raises 429: If rate limit exceeded.
    """
    post_id_int = validate_post_id(post_id)
    post = get_post_by_id(post_id_int, posts)
    comment_data = request.get_json()
    comment = comment_data.get("comment", "").strip()

    if not comment:
        abort(400, description="Comment cannot be empty")

    if "comments" not in post:
        post["comments"] = []
    post["comments"].append(comment)

    save_data_to_json(posts)
    return jsonify({"message": "Comment added successfully", "post": post}), 200


if __name__ == "__main__":
    posts = fetch_data_from_json()
    app.run(host="0.0.0.0", port=5002, debug=True)
