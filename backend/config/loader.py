"""
loader.py

This module provides configuration loading utilities for the Masterblog API.
It includes functions to load JSON-based config files and suppress development warnings.

Functions:
- load_config(path): Loads the main configuration from a given or default JSON file path.
- apply_runtime_config(): Suppresses specific development warnings during runtime.

Author: Martin Haferanke
Date: 2025-06-30
"""

import json
from pathlib import Path
import warnings


def load_config(path: str = None) -> dict:
    """
    Load a configuration dictionary from a JSON file.

    :param path: Path to the configuration file. Defaults to 'config.json' in the current directory.
    :return: Parsed configuration data as a dictionary.

    :raises FileNotFoundError: If the configuration file does not exist.
    :raises ValueError: If the file contains invalid JSON.
    :raises RuntimeError: For all other unexpected errors during loading.
    """
    try:
        if path is None:
            path = Path(__file__).parent / "config.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Configuration file not found at path: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file at path {path}: {e}") from e
    except Exception as e:
        raise RuntimeError(
            f"Unexpected error loading config file at {path}: {e}"
        ) from e


def apply_runtime_config():
    """
    Apply runtime settings to suppress development warnings.

    This currently filters out in-memory warnings from flask_limiter.
    """
    # Suppress in-memory warning from flask_limiter in dev
    warnings.filterwarnings("ignore", category=UserWarning, module="flask_limiter")
