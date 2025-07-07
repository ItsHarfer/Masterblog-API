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
    path = Path(__file__).parent.parent / "data" / "posts.json"

    if not path.exists():
        logging.warning(f"Data file does not exist at {path}. Returning empty list.")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)
            for post in posts:
                post.setdefault("comments", [])
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
    Saves the list of data to the JSON file.

    :param data: List of data to save.

    :raises OSError: If there is an OS-related file access error.
    :raises IOError: If the file cannot be written to.
    :raises TypeError: If the data cannot be serialized to JSON.
    :raises Exception: For all other unexpected errors.
    """
    # Define the path to the JSON file
    path = Path(__file__).parent.parent / "data" / "posts.json"

    # Ensure the directory exists, create if necessary
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Could not create directory for {path.parent}: {e}")

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            logging.info(f"Successfully wrote data to {path}")
    except (OSError, IOError) as e:
        logging.error(f"Failed to write JSON to {path}: {e}")
    except TypeError as e:
        logging.error(f"Data serialization failed while writing to {path}: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error while writing JSON to {path}: {e}")
