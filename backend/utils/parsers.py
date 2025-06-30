"""
utils / parsers.py

This module provides functions for parsing and sanitizing incoming request data from Flask.
It prioritizes JSON body fields over query parameters and helps standardize input handling.

Functions:
- parse_post_field_input(): Extracts 'title', 'content', 'author', and 'date' fields from request body or query params.
- parse_sort_query_input(): Extracts 'sort' and 'direction' values from query params.

Author: Martin Haferanke
Date: 2025-06-30
"""

from flask import request


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
