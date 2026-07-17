"""
Main Flask routes and application logic for YouTube Downloader.

This module contains all the Flask routes, request handling,
and integration between frontend and backend services.
"""

import logging

from flask import Blueprint, render_template, request, send_file, session

from .services.youtube_service import YouTubeService
from .utils.helpers import format_video_length

# Setup logger
logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def home():
    """Handle the main page and all user interactions."""
    # Initialize session variables
    session["thumbnail"] = ""
    session["title"] = ""
    session["visibility"] = "hidden"
    session["resolutions"] = ""
    session["videoLength"] = ""

    if request.method == "POST":
        url_text = request.form.get("search_url", "")

        # Handle search functionality
        if "search" in request.form:
            if "search_url" in request.form and "https" in url_text.lower():
                try:
                    logger.info(f"Searching for video: {url_text}")

                    session["stored_url"] = url_text

                    youtube_service = YouTubeService()
                    youtube_data = youtube_service.get_video_info(url_text)

                    if not youtube_data:
                        return render_template(
                            "index.html", error="Failed to fetch video information"
                        )

                    # Store video data in session
                    session["thumbnail"] = youtube_data.thumbnail_url
                    session["title"] = youtube_data.title
                    session["visibility"] = "visible"
                    session["videoLength"] = (
                        f"Video Length: {format_video_length(youtube_data.length)}"
                    )
                    session["resolutions"] = youtube_service.get_video_resolutions(
                        url_text
                    )

                    logger.info(
                        f"Successfully fetched video info for: {youtube_data.title}"
                    )

                except Exception as e:
                    logger.error(f"Error during search: {e}")
                    return render_template(
                        "index.html", error="Failed to fetch video information"
                    )

        # Handle video download
        elif "download_button_mine" in request.form:
            try:
                url = session.get("stored_url")
                if not url:
                    return "Invalid URL", 400

                selected_resolution = request.form.get("resolutions")
                if not selected_resolution:
                    return "No resolution selected", 400

                logger.info(
                    f"Downloading video: {url} at resolution: {selected_resolution}"
                )

                youtube_service = YouTubeService()
                video_buffer = youtube_service.download_video_to_buffer(
                    url, selected_resolution
                )

                if not video_buffer:
                    return "Error processing video", 500

                # Get video title for filename
                youtube_data = youtube_service.get_video_info(url)
                if not youtube_data:
                    return "Failed to get video info", 500

                logger.info(f"Video download completed: {youtube_data.title}")

                return send_file(
                    video_buffer,
                    as_attachment=True,
                    download_name=f"{youtube_data.title}.mp4",
                    mimetype="video/mp4",
                )
            except Exception as e:
                logger.error(f"Error during video download: {e}")
                return "Error processing video", 500

        # Handle audio download
        elif "download_audio_button_mine" in request.form:
            try:
                url = session.get("stored_url")
                if not url:
                    return "Invalid URL", 400

                logger.info(f"Downloading audio: {url}")

                youtube_service = YouTubeService()
                mp3_buffer = youtube_service.download_audio_to_buffer(url)

                if not mp3_buffer:
                    return "Error processing audio", 500

                # Get video title for filename
                youtube_data = youtube_service.get_video_info(url)
                if not youtube_data:
                    return "Failed to get video info", 500

                logger.info(f"Audio download completed: {youtube_data.title}")

                return send_file(
                    mp3_buffer,
                    as_attachment=True,
                    download_name=f"{youtube_data.title}.mp3",
                    mimetype="audio/mpeg",
                )
            except Exception as e:
                logger.error(f"Error during audio download: {e}")
                return "Error processing audio", 500

    # Render the main page with current session data
    return render_template(
        "index.html",
        thumbnail=session.get("thumbnail"),
        title=session.get("title"),
        un_visible=session.get("visibility"),
        res_visibility=session.get("visibility"),
        resolutions=session.get("resolutions"),
        videoLength=session.get("videoLength"),
    )
