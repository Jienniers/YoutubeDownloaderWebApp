"""
YouTube Downloader Web Application Package

This package contains all components needed to run the YouTube video and audio downloader web application.
"""

import os
import secrets

from flask import Flask


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=os.path.join("..", "templates"),
        static_folder=os.path.join("..", "static"),
    )
    app.secret_key = secrets.token_hex(16)

    from .main import main_bp

    app.register_blueprint(main_bp)

    return app
