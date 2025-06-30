"""
utils / json_io.py

This module manages reading from and writing to the JSON data store (posts.json).

Functions:
- fetch_data_from_json(): Loads post data from file and ensures presence of 'comments' key.
- save_data_to_json(data): Writes updated post data back to file with error logging.

Author: Martin Haferanke
Date: 2025-06-30
"""

import json
import logging
from pathlib import Path


def fetch_data_from_json() -> list:
    """
    Fetches and returns data from a JSON file.

    :return: The content of the JSON file as a list of posts.

    :raises json.JSONDecodeError: If the file contains invalid JSON.
    :raises ValueError: If a decoding issue occurs.
    :raises UnicodeDecodeError: If the file cannot be decoded.
    :raises OSError: If there is an OS-related file access error.
    :raises IOError: If there is an input/output error accessing the file.
    :raises Exception: For all other unexpected errors.
    """
    path = Path(__file__).parent / "data" / "posts.json"

    if not path.exists():
        logging.warning(f"Data file does not exist at {path}. Returning empty list.")
        return []

    try:
        with open(path, "r") as f:
            posts = json.load(f)
            for post in posts:
                if "comments" not in post:
                    post["comments"] = []
            return posts
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

    :raises OSError: If there is an OS-related file access error.
    :raises IOError: If the file cannot be written to.
    :raises TypeError: If the data cannot be serialized to JSON.
    :raises Exception: For all other unexpected errors.
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
