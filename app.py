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


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

INVALID_CHARACTERS = r'[<>:"/\\|?*]'

# Reserved words that cannot be used as filenames in Windows
RESERVED_WORDS = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

# Regex pattern to match emojis based on common emoji Unicode ranges
EMOJI_PATTERN = (
    r"[\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    r"\U0001F700-\U0001F77F"  # Alchemical Symbols
    r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    r"\U0001FA00-\U0001FA6F"  # Chess Symbols
    r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    r"\U00002702-\U000027B0"  # Dingbats
    r"\U0001F004-\U0001F0CF"  # Playing Cards
    r"\U00002B50]"  # Star symbol
)


def sanitize_filename(filename):
    # Remove invalid characters
    filename = re.sub(INVALID_CHARACTERS, "", filename)

    # Remove emojis using the defined emoji pattern
    filename = re.sub(EMOJI_PATTERN, "", filename)

    # Remove any non-ASCII characters (excluding emojis that may already be removed)
    filename = "".join(c for c in filename if ord(c) < 128)

    # Remove leading/trailing spaces
    filename = filename.strip()

    # Handle reserved filenames (e.g., "CON")
    base, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
    if base.upper() in RESERVED_WORDS:
        base = base + "_"

    # Reassemble the filename with the extension
    sanitized_filename = f"{base}.{ext}" if ext else base
    return sanitized_filename


def downloadVideo(url, selectedResolution):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)

        videoStreams = yt.streams.filter(res=selectedResolution).first()
        audioStreams = yt.streams.filter(only_audio=True).first()

        if videoStreams and audioStreams:
            print(f"Downloading: {yt.title}")
            print(f"Downloading {videoStreams.resolution} resolution...")

            newFileName = sanitize_filename(yt.title)

            # Ensure Videos directory exists
            os.makedirs("Videos", exist_ok=True)

            video_thread = threading.Thread(
                target=lambda: videoStreams.download(
                    "Videos/",
                    filename=f"{newFileName}.mp4",
                )
            )

            audio_thread = threading.Thread(
                target=lambda: audioStreams.download(
                    "Videos/", filename=f"{newFileName}.mp3"
                )
            )

            video_thread.start()
            audio_thread.start()

            video_thread.join()
            audio_thread.join()

            print("\nDone Downloading Video")

            videoPath = os.path.join("Videos", f"{newFileName}.mp4")
            audioPath = os.path.join("Videos", f"{newFileName}.mp3")
            outputPath = os.path.join("Videos", "Final " + newFileName + ".mp4")

            # Ensure Videos directory exists before merging (redundant but safe)
            os.makedirs("Videos", exist_ok=True)

            video_clip = ffmpeg.input(videoPath)
            audio_clip = ffmpeg.input(audioPath)

            num_threads = os.cpu_count()

            ffmpeg.concat(video_clip, audio_clip, v=1, a=1).output(
                outputPath, threads=num_threads
            ).run(overwrite_output=True)

            print("Merging complete!")

            print(f"Orignal VideoPath: {videoPath}")
            print(f"Orignal AudioPath: {audioPath}")
            print(f"Orignal OutputPath: {outputPath}")

            return outputPath
        else:
            print("No streams available for the video.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def downloadAudio(url):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)

        audioStreams = yt.streams.filter(only_audio=True).first()

        if audioStreams:
            newFileName = sanitize_filename(yt.title)

            # Ensure Audios directory exists
            os.makedirs("Audios", exist_ok=True)

            audioPath = audioStreams.download(
                output_path="Audios/", filename=f"{newFileName}.m4a"
            )

            print("\nDone Downloading Audio")

            outputPath = os.path.join("Audios", f"{newFileName}.mp3")

            # Ensure Audios directory exists before conversion (redundant but safe)
            os.makedirs("Audios", exist_ok=True)

            ffmpeg.input(audioPath).output(outputPath, acodec="libmp3lame").run()

            os.remove(audioPath)

            print(f"Audio converted and saved as {outputPath}")

            return outputPath

    except Exception as e:
        print(f"Error: {e}")
        return None


def deleteVideoFileAfterDelay(delay_seconds=5):
    time.sleep(delay_seconds)
    if os.path.exists("Videos"):
        shutil.rmtree("Videos")


def deleteAudioFileAfterDelay(delay_seconds=5):
    time.sleep(delay_seconds)
    if os.path.exists("Audios"):
        shutil.rmtree("Audios")


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

                session["videoLenght"] = (
                    f"Video Length: {get_video_length(youtube)}"
                )

                session["resolutions"] = get_video_resolutions(
                    session.get("stored_url")
                )

                print("Available resolutions:", session.get("resolutions"))

        elif "download_button_mine" in request.form:
            print(session.get("stored_url"))

            selectedResolution = request.form["resolutions"]

            videoPath = downloadVideo(session.get("stored_url"), selectedResolution)

            if videoPath is None:
                return "Please Try again! Error occured", 404

            newVideoPath = videoPath.replace("Final ", "")

            if os.path.exists(videoPath):
                os.replace(videoPath, newVideoPath)
                print(f"File renamed to: {newVideoPath}")

            else:
                print(f"Error: The file at {videoPath} does not exist.")

            if newVideoPath:

                @after_this_request
                def remove_file(response):
                    threading.Thread(target=deleteVideoFileAfterDelay).start()
                    return response

                return send_file(
                    newVideoPath,
                    as_attachment=True,
                    download_name=os.path.basename(newVideoPath),
                )
            else:
                return "Video File download failed, " "Please try any other video.", 404

        elif "download_audio_button_mine" in request.form:
            print(session.get("stored_url"))

            audioPath = downloadAudio(session.get("stored_url"))

            if audioPath is None:
                return "Please Try again! Error occured", 404

            if os.path.exists(audioPath):

                @after_this_request
                def remove_file(response):
                    threading.Thread(target=deleteAudioFileAfterDelay).start()
                    return response

                return send_file(
                    audioPath,
                    as_attachment=True,
                    download_name=os.path.basename(audioPath),
                )

            else:
                return "Audio File download failed, " "Please try any other audio.", 404

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
