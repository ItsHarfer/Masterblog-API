"""
app_factory.py

This module defines the Flask application factory and configures core extensions including CORS, Swagger UI, and rate limiting.
It also sets up logging and applies runtime configuration settings.

Functions:
- create_app(): Initializes and returns the Flask app, limiter, and configuration.

Author: Martin Haferanke
Date: 2025-06-30
"""

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from config.loader import load_config, apply_runtime_config

import logging


def create_app():
    """
    Create and configure the Flask application with CORS, Swagger UI, rate limiting, and logging.

    :return: A tuple containing the configured Flask app, the Limiter instance, and the loaded configuration.
    :rtype: tuple[Flask, Limiter, dict]
    """
    app = Flask(__name__)
    CORS(app)

    # For dev purposes deactivate limiter warnings
    apply_runtime_config()

    # Loading constants
    config = load_config()

    # Swagger setup
    swagger_cfg = config["swagger"]
    swagger_ui = get_swaggerui_blueprint(
        swagger_cfg["url"],
        swagger_cfg["api_url"],
        config=swagger_cfg["config"],
    )
    app.register_blueprint(swagger_ui, url_prefix=swagger_cfg["url"])

    # Rate limiter
    limiter = Limiter(get_remote_address, app=app, default_limits=["100 per hour"])

    # Logging
    logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return app, limiter, config
