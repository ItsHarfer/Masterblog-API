"""
utils / helpers.py

This module provides utility functions for accessing blog post content.

Functions:
- get_post_by_id(post_id, posts): Searches for and returns a post by ID or aborts with 404 if not found.

Author: Martin Haferanke
Date: 2025-06-30
"""

from flask import abort


def get_post_by_id(post_id, posts):
    """
    Find and return the post by ID.

    :param posts:
    :param post_id: The ID of the post to find
    :return: The post object if found.
    :raises: 404: If no post with the given ID exists.
    """
    post = next((post for post in posts if post["id"] == post_id), None)
    if not post:
        return abort(404, description=f"Post with id {post_id} not found.")
    return post
