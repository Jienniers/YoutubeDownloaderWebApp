#!/usr/bin/env python3
"""
Main application entry point for YouTube Downloader.

This script initializes and runs the Flask web application.
"""

import logging
from youtube_downloader import create_app

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    app = create_app()

    # Run the Flask application
    logger.info("Starting YouTube Downloader application")
    app.run(debug=False, host="0.0.0.0", threaded=True)
