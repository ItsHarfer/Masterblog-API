"""
frontend_app.py

This module defines the Flask frontend application for rendering the homepage of the Masterblog API.
It serves the main HTML interface via a single route.

Functions:
- home(): Renders and returns the 'index.html' template when the root URL is accessed.

Author: Martin Haferanke
Date: 2025-06-30
"""

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)
