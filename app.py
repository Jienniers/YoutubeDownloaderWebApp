import os
import threading
import time
import shutil
import sys
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from pytubefix.cli import on_progress
    from pytubefix import YouTube
except ImportError:
    print("Module 'pytubefix' is not installed. Installing now.")
    install('pytubefix')
    try:
        from pytubefix.cli import on_progress
        from pytubefix import YouTube
    except ImportError as e:
        print(f"Failed to import 'pytubefix' after installation: {e}")
        sys.exit(1)

try:
    from flask import Flask, render_template, request, send_file, after_this_request
except ImportError:
    if sys.platform.startswith("win"):
        os.system("python -m pip install flask")
    else:
        os.system("python3 -m pip install flask")
    try:
        from flask import Flask, render_template, request, send_file, after_this_request
    except ImportError:
        print("You need python3 installed! Main")
        exit()


# try:
#     from moviepy.editor import VideoFileClip, AudioFileClip
# except ImportError:
#     if sys.platform.startswith("win"):
#         os.system("python -m pip install moviepy")
#     else:
#         os.system("python3 -m pip install moviepy")
#     try:
#         from moviepy.editor import VideoFileClip, AudioFileClip
#     except ImportError:
#         print("You need python3 installed! Main")
#         exit()



try:
    import ffmpeg
except ImportError:
    if sys.platform.startswith("win"):
        os.system("python -m pip install ffmpeg-python")
    else:
        os.system("python3 -m pip install ffmpeg-python")
    try:
        import ffmpeg
    except ImportError:
        print("You need python3 installed! Main")
        exit()

app = Flask(__name__)

def downloadVideo(url, selectedResolution):
    try:
        yt = YouTube(url, use_po_token=True, on_progress_callback = on_progress)

        videoStreams = yt.streams.filter(res=selectedResolution).first()
        audioStreams = yt.streams.filter(only_audio=True).first()

        if videoStreams and audioStreams:

            print(f"Downloading: {yt.title}")
            print(f"Downloading {videoStreams.resolution} resolution...")


            videoStreams.download("Videos/")
            audioStreams.download("Videos/")

            print("\nDone Downloading")

            VideoFileName = videoStreams.default_filename
            AudioFileName = audioStreams.default_filename

            if '|' in VideoFileName: 
                VideoFileName = VideoFileName.replace('|', '')

            if ':' in VideoFileName:
                VideoFileName = VideoFileName.replace(':', '')

            if '*' in VideoFileName:
                VideoFileName = VideoPath.replace('*', '')

            if '?' in VideoFileName:
                VideoFileName = VideoFileName.replace('?', '')

            if '"' in VideoFileName:
                VideoFileName = VideoFileName.replace('"', '')

            if '<' in VideoFileName:
                VideoFileName = VideoFileName.replace('<', '')

            if '>' in VideoFileName:
                VideoFileName = VideoFileName.replace('>', '')

            if '/' in VideoFileName:
                VideoFileName = VideoFileName.replace('/', '')

            if "\\" in VideoFileName:
                VideoFileName = VideoFileName.replace("\\", "")

                #Audio Path

            if '|' in AudioFileName: 
                AudioFileName = AudioFileName.replace('|', '')

            if ':' in AudioFileName:
                AudioFileName = AudioFileName.replace(':', '')

            if '*' in AudioFileName:
                AudioFileName = AudioFileName.replace('*', '')

            if '?' in AudioFileName:
                AudioFileName = AudioFileName.replace('?', '')

            if '"' in AudioFileName:
                AudioFileName = AudioFileName.replace('"', '')

            if '<' in AudioFileName:
                AudioFileName = AudioFileName.replace('<', '')

            if '>' in AudioFileName:
                AudioFileName = AudioFileName.replace('>', '')

            if '/' in AudioFileName:
                AudioFileName = AudioFileName.replace('/', '')

            if "\\" in AudioFileName:
                AudioFileName = AudioFileName.replace("\\", "")

            VideoPath = os.path.join('Videos', VideoFileName)
            AudioPath = os.path.join('Videos', AudioFileName)
            OutputPath = os.path.join('Videos', "Final " + VideoFileName)


            # video_clip = VideoFileClip(VideoPath)
            # audio_clip = AudioFileClip(AudioPath)

            # final_clip = video_clip.set_audio(audio_clip)

            # final_clip.write_videofile(OutputPath, codec="libx264", audio_codec="aac")

            video_clip = ffmpeg.input(VideoPath)

            audio_clip = ffmpeg.input(AudioPath)

            ffmpeg.concat(video_clip, audio_clip, v=1, a=1).output(OutputPath).run()
            

            print("Merging complete!")

            print(f"VideoPath: {VideoPath}")
            print(f"AudioPath: {AudioPath}")
            print(f"SoundPath: {OutputPath}")

            return "Videos\\" + "Final " + videoStreams.default_filename
        else:
            print("No streams available for the video.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    

def downloadAudio(url):
    try:
        yt = YouTube(url, use_po_token=True, on_progress_callback = on_progress)

        audioStreams = yt.streams.filter(only_audio=True).first()

        if audioStreams:
            audioStreams.download('Audios/')

            # audio = AudioFileClip(f"Audios/{audioStreams.default_filename}")

            # # Ensure the file extension matches the codec
            output_filename = f"Audios/Final-{audioStreams.default_filename.replace('.m4a', '.mp3')}"

            # # Write the audio to an MP3 file
            # audio.write_audiofile(output_filename, codec='mp3')
            input_file = f"Audios/{audioStreams.default_filename}"

            ffmpeg.input(input_file).output(output_filename, acodec='libmp3lame', ar='44100', ac=2, ab='192k').run(overwrite_output=True)

            return output_filename

    except Exception as e:
        print(f"Error: {e}")
        return None

def deleteVideoFileAfterDelay(delay_seconds=5):
    time.sleep(delay_seconds)
    shutil.rmtree("Videos")


def deleteAudioFileAfterDelay(delay_seconds=5):
    time.sleep(delay_seconds)
    shutil.rmtree("Audios")


def get_video_resolutions(video_url):
    yt = YouTube(video_url)
    stream_list = yt.streams.filter(file_extension='mp4')
    
    resolutions = [stream.resolution for stream in stream_list if stream.resolution]
    # Remove duplicates, sort resolutions, and order them by quality
    resolutions = list(sorted(set(resolutions), key=lambda x: int(x[:-1]), reverse=True))
    return resolutions

stored_url = ""
@app.route('/', methods=['GET', 'POST'])
def home():
    global stored_url
    thumbnail = ""
    title = ""
    visibility = "hidden"
    resolutions = ""
    if request.method == 'POST':
        url_text = request.form['search_url']

        if 'search' in request.form:
            if 'search_url' in request.form and 'https' in url_text.lower():
                stored_url = url_text
                print(stored_url)
                youtube = YouTube(url_text, use_po_token=True)
                thumbnail = youtube.thumbnail_url
                title = f"{youtube.title}"
                visibility = "visible"

                resolutions = get_video_resolutions(stored_url)

                print("Available resolutions:", resolutions)

        elif "download_button_mine" in request.form:
            print(stored_url)
            selectedResolution = request.form['resolutions']
            videoPath = downloadVideo(stored_url, selectedResolution)

            print(videoPath)

            if videoPath:
                @after_this_request
                def remove_file(response):
                    threading.Thread(target=deleteVideoFileAfterDelay).start()
                    return response

                return send_file(
                    videoPath,
                    as_attachment=True,
                    download_name=os.path.basename(videoPath)
                )
            else:
                return "Video File download failed", 404
            
        elif "download_audio_button_mine" in request.form:

            audioPath = downloadAudio(stored_url)

            if os.path.exists(audioPath):

                @after_this_request
                def remove_file(response):
                    threading.Thread(target=deleteAudioFileAfterDelay).start()
                    return response
            
                return send_file(
                    audioPath,
                    as_attachment=True,
                    download_name=os.path.basename(audioPath)
                )

            else:
                return "Audio File download failed", 404
            
    return render_template(
        'index.html', 
        thumbnail=thumbnail, 
        title=title, 
        un_visible=visibility,
        res_visibility=visibility,
        resolutions=resolutions)


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")