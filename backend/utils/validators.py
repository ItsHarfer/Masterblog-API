"""
utils / validators.py

This module provides validation functions for request parameters to ensure input integrity.

Functions:
- validate_post_id(post_id): Validates that a given post_id is an integer.
- get_field_error_response(title, content, author, date): Checks for missing fields and aborts with descriptive error.

Author: Martin Haferanke
Date: 2025-06-30
"""

from datetime import datetime

from flask import abort


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


def validate_date_string(date_str: str, post_id=None) -> datetime:
    """
    Parse a date string in YYYY-MM-DD format or abort with 400.
    :param date_str: the date to validate
    :param post_id: optional
    :return: parsed datetime.date
    """
    if not date_str:
        abort(400, description=f"Missing date for post id {post_id}")
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        abort(
            400,
            description=(
                f"Invalid date format for post id {post_id}: '{date_str}', "
                "expected YYYY-MM-DD"
            ),
        )
