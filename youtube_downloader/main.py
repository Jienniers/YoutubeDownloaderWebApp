"""
Main Flask routes and application logic for YouTube Downloader.

This module contains all the Flask routes, request handling,
and integration between frontend and backend services.
"""

import logging
import threading
import uuid

from flask import Blueprint, jsonify, render_template, request, send_file, session

from .services.youtube_service import YouTubeService
from .utils.helpers import format_video_length

# Setup logger
logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)
_jobs = {}
_jobs_lock = threading.Lock()


def _run_video_job(job_id, url, resolution):
    with _jobs_lock:
        job = _jobs[job_id]
        job["status"] = "processing"
    try:
        if _job_cancelled(job_id):
            with _jobs_lock:
                _jobs[job_id]["status"] = "cancelled"
            return
        service = YouTubeService()
        info = service.get_video_info(url)
        if not info:
            raise RuntimeError("Could not read video information")
        if _job_cancelled(job_id):
            with _jobs_lock:
                _jobs[job_id]["status"] = "cancelled"
            return
        with _jobs_lock:
            _jobs[job_id]["title"] = info.title
        buffer = service.download_video_to_buffer(
            url, resolution,
            progress_callback=lambda percent: _update_progress(job_id, percent),
            cancel_check=lambda: _job_cancelled(job_id),
        )
        if not buffer:
            if _job_cancelled(job_id):
                with _jobs_lock:
                    _jobs[job_id].update(status="cancelled", progress=0)
                return
            raise RuntimeError("Video processing failed")
        with _jobs_lock:
            if _jobs[job_id]["cancel_event"].is_set():
                _jobs[job_id].update(status="cancelled", progress=0)
                return
            _jobs[job_id].update(status="complete", progress=100, buffer=buffer,
                                 filename=f"{info.title}.mp4", mimetype="video/mp4")
    except Exception as error:
        logger.exception("Video job %s failed", job_id)
        with _jobs_lock:
            _jobs[job_id].update(status="error", error=str(error))


def _run_audio_job(job_id, url):
    with _jobs_lock:
        _jobs[job_id]["status"] = "processing"
    try:
        if _job_cancelled(job_id):
            with _jobs_lock:
                _jobs[job_id]["status"] = "cancelled"
            return
        service = YouTubeService()
        info = service.get_video_info(url)
        if not info:
            raise RuntimeError("Could not read video information")
        if _job_cancelled(job_id):
            with _jobs_lock:
                _jobs[job_id]["status"] = "cancelled"
            return
        with _jobs_lock:
            _jobs[job_id]["title"] = info.title
        buffer = service.download_audio_to_buffer(
            url,
            progress_callback=lambda percent: _update_progress(job_id, percent),
            cancel_check=lambda: _job_cancelled(job_id),
        )
        if not buffer:
            if _job_cancelled(job_id):
                with _jobs_lock:
                    _jobs[job_id].update(status="cancelled", progress=0)
                return
            raise RuntimeError("Audio processing failed")
        with _jobs_lock:
            if _jobs[job_id]["cancel_event"].is_set():
                _jobs[job_id].update(status="cancelled", progress=0)
                return
            _jobs[job_id].update(status="complete", progress=100, buffer=buffer,
                                 filename=f"{info.title}.mp3", mimetype="audio/mpeg")
    except Exception as error:
        logger.exception("Audio job %s failed", job_id)
        with _jobs_lock:
            _jobs[job_id].update(status="error", error=str(error))


def _job_cancelled(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
        return not job or job["cancel_event"].is_set()


def _update_progress(job_id, percent):
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id]["progress"] = round(percent)


@main_bp.route("/api/video-download", methods=["POST"])
def start_video_download():
    payload = request.get_json(silent=True) or {}
    url, resolution = payload.get("url"), payload.get("resolution")
    if not url or not resolution:
        return jsonify(error="A video URL and resolution are required."), 400
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {"status": "queued", "progress": 0, "buffer": None,
                         "cancel_event": threading.Event()}
    threading.Thread(target=_run_video_job, args=(job_id, url, resolution), daemon=True).start()
    return jsonify(jobId=job_id), 202


@main_bp.route("/api/video-download/<job_id>/cancel", methods=["POST"])
@main_bp.route("/api/audio-download/<job_id>/cancel", methods=["POST"])
def cancel_video_download(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return jsonify(error="Download job not found."), 404
        if job["status"] in {"complete", "error", "cancelled"}:
            return jsonify(status=job["status"]), 409
        job["cancel_event"].set()
        job["status"] = "cancelling"
    return jsonify(status="cancelling"), 202


@main_bp.route("/api/audio-download", methods=["POST"])
def start_audio_download():
    payload = request.get_json(silent=True) or {}
    url = payload.get("url")
    if not url:
        return jsonify(error="A video URL is required."), 400
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {"status": "queued", "progress": 0, "buffer": None,
                         "cancel_event": threading.Event()}
    threading.Thread(target=_run_audio_job, args=(job_id, url), daemon=True).start()
    return jsonify(jobId=job_id), 202


@main_bp.route("/api/video-info", methods=["POST"])
def video_info():
    payload = request.get_json(silent=True) or {}
    url = payload.get("url", "")
    if not url.lower().startswith("https://"):
        return jsonify(error="Enter a valid HTTPS video URL."), 400
    service = YouTubeService()
    info = service.get_video_info(url)
    if not info:
        return jsonify(error="Could not fetch video information."), 400
    session["stored_url"] = url
    return jsonify(title=info.title, thumbnail=info.thumbnail_url,
                   length=format_video_length(info.length),
                   resolutions=service.get_video_resolutions(url))


@main_bp.route("/api/video-download/<job_id>")
@main_bp.route("/api/audio-download/<job_id>")
def video_download_status(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return jsonify(error="Download job not found."), 404
        return jsonify(status=job["status"], progress=job["progress"],
                       title=job.get("title", ""), error=job.get("error", ""))


@main_bp.route("/api/video-download/<job_id>/file")
@main_bp.route("/api/audio-download/<job_id>/file")
def video_download_file(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job or job["status"] != "complete":
            return jsonify(error="The video is not ready yet."), 409
        buffer, filename = job["buffer"], job["filename"]
        mimetype = job.get("mimetype", "video/mp4")
    response = send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)

    def discard_job():
        with _jobs_lock:
            _jobs.pop(job_id, None)

    response.call_on_close(discard_job)
    return response


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

                return "Video downloads must be started from the download queue.", 400
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
