import os
import threading
import time
import shutil
import re
import secrets
from pytubefix.cli import on_progress
from pytubefix import YouTube
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    after_this_request,
    session,
)
import ffmpeg
import io
import tempfile


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


def download_video_to_buffer(url, selected_resolution):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)

        video_stream = yt.streams.filter(res=selected_resolution, progressive=False, file_extension="mp4").first()
        audio_stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()

        if not video_stream or not audio_stream:
            print("Streams not found")
            return None

        # Step 1: Save both streams to temporary files
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_temp:
            video_temp_path = video_temp.name
            video_stream.stream_to_buffer(video_temp)
            video_temp.flush()

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as audio_temp:
            audio_temp_path = audio_temp.name
            audio_stream.stream_to_buffer(audio_temp)
            audio_temp.flush()

        # Step 2: Merge using ffmpeg-python into a new temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_temp:
            output_temp_path = output_temp.name

        (
            ffmpeg
            .input(video_temp_path)
            .output(
                output_temp_path,
                **{'i': audio_temp_path},
                c='copy',
                loglevel='quiet'
            )
            .run(overwrite_output=True)
        )

        # Step 3: Load result into memory buffer
        video_buffer = io.BytesIO()
        with open(output_temp_path, "rb") as f:
            video_buffer.write(f.read())
        video_buffer.seek(0)

        # Step 4: Clean up all temp files
        os.remove(video_temp_path)
        os.remove(audio_temp_path)
        os.remove(output_temp_path)

        return video_buffer

    except Exception as e:
        print(f"[ERROR] Video download/merge failed: {e}")
        return None
    

def deleteVideoFileAfterDelay(delay_seconds=5):
    time.sleep(delay_seconds)
    if os.path.exists("Videos"):
        shutil.rmtree("Videos")


def get_video_resolutions(video_url):
    yt = YouTube(video_url)
    stream_list = yt.streams.filter(file_extension="mp4")

    resolutions = [stream.resolution for stream in stream_list if stream.resolution]
    # Remove duplicates, sort resolutions, and order them by quality
    resolutions = list(
        sorted(set(resolutions), key=lambda x: int(x[:-1]), reverse=True)
    )
    return resolutions


def get_video_length(youtube: YouTube):
    vidLength = youtube.length

    minutes = vidLength // 60
    seconds = vidLength % 60

    formatted_length = f"{minutes:02}:{seconds:02}"
    return formatted_length


def download_audio_to_buffer(audio_stream):
    try:
        # Step 1: Write audio stream to a temp .mp4 file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_input:
            temp_input_path = temp_input.name
            audio_stream.stream_to_buffer(temp_input)
            temp_input.flush()

        # Step 2: Create temp output path for .mp3
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_output:
            temp_output_path = temp_output.name

        # Step 3: Convert to MP3 using ffmpeg-python
        (
            ffmpeg
            .input(temp_input_path)
            .output(temp_output_path, format='mp3', acodec='libmp3lame', audio_bitrate='192k', ar='44100', loglevel='quiet')
            .run(overwrite_output=True)
        )

        # Step 4: Load converted audio into memory buffer
        mp3_buffer = io.BytesIO()
        with open(temp_output_path, "rb") as f:
            mp3_buffer.write(f.read())
        mp3_buffer.seek(0)

        # Step 5: Cleanup temp files
        os.remove(temp_input_path)
        os.remove(temp_output_path)

        return mp3_buffer

    except Exception as e:
        print(f"[ERROR] Audio conversion failed: {e}")
        return None


@app.route("/", methods=["GET", "POST"])
def home():
    session["thumbnail"] = ""
    session["title"] = ""
    session["visibility"] = "hidden"
    session["resolutions"] = ""
    session["videoLength"] = ""

    if request.method == "POST":
        url_text = request.form["search_url"]

        if "search" in request.form:
            if "search_url" in request.form and "https" in url_text.lower():
                session["stored_url"] = url_text

                print(session.get("stored_url"))

                youtube = YouTube(url_text)

                session["thumbnail"] = youtube.thumbnail_url

                session["title"] = f"{youtube.title}"

                session["visibility"] = "visible"

                session["videoLenght"] = f"Video Length: {get_video_length(youtube)}"

                session["resolutions"] = get_video_resolutions(
                    session.get("stored_url")
                )

                print("Available resolutions:", session.get("resolutions"))

        elif "download_button_mine" in request.form:
            url = session.get("stored_url")

            print(url)

            selectedResolution = request.form["resolutions"]

            video_buffer = download_video_to_buffer(url, selectedResolution)

            if video_buffer:
                yt = YouTube(url)
                return send_file(
                    video_buffer,
                    as_attachment=True,
                    download_name=f"{yt.title}.mp4",
                    mimetype="video/mp4"
                )
            else:
                return "Error processing video", 500
            

        elif "download_audio_button_mine" in request.form:
            url = session.get("stored_url")
            print(url)

            yt = YouTube(url)

            audio_stream = (
                yt.streams.filter(only_audio=True, file_extension="mp4")
                .order_by("abr")
                .desc()
                .first()
            )

            mp3_buffer = download_audio_to_buffer(audio_stream)

            return send_file(
                mp3_buffer,
                as_attachment=True,
                download_name=f"{yt.title}.mp3",
                mimetype="audio/mpeg",
            )

    return render_template(
        "index.html",
        thumbnail=session.get("thumbnail"),
        title=session.get("title"),
        un_visible=session.get("visibility"),
        res_visibility=session.get("visibility"),
        resolutions=session.get("resolutions"),
        videoLength=session.get("videoLenght"),
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", threaded=True)
