"""
YouTube Service for downloading videos and audio from YouTube.

This service handles all the core functionality related to 
fetching video information, downloading streams, merging video/audio,
and converting audio formats.
"""

import io
import os
import tempfile
import logging
from typing import Optional, List, BinaryIO
from pytubefix import YouTube
from pytubefix.cli import on_progress
import ffmpeg

from ..models.video_info import VideoInfo
from ..utils.exceptions import DownloadError, ConversionError

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service class for handling YouTube video and audio download operations."""
    
    def __init__(self):
        """Initialize the YouTube service with default configurations."""
        pass
    
    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        Fetch basic information about a YouTube video.
        
        Args:
            url (str): The URL of the YouTube video
            
        Returns:
            VideoInfo: Object containing video metadata or None if failed
        """
        try:
            yt = YouTube(url, on_progress_callback=on_progress)
            
            # Create and return VideoInfo object
            video_info = VideoInfo(
                title=yt.title,
                thumbnail_url=yt.thumbnail_url,
                length=yt.length
            )
            
            logger.info(f"Fetched video info for: {video_info.title}")
            return video_info
            
        except Exception as e:
            logger.error(f"Failed to get video info from URL {url}: {e}")
            return None
    
    def get_video_resolutions(self, video_url: str) -> List[str]:
        """
        Get available resolutions for a YouTube video.
        
        Args:
            video_url (str): The URL of the YouTube video
            
        Returns:
            List[str]: List of available resolutions
        """
        try:
            yt = YouTube(video_url)
            stream_list = yt.streams.filter(file_extension="mp4")
            
            resolutions = [stream.resolution for stream in stream_list if stream.resolution]
            # Remove duplicates, sort resolutions, and order them by quality
            resolutions = list(
                sorted(set(resolutions), key=lambda x: int(x[:-1]), reverse=True)
            )
            
            logger.info(f"Found {len(resolutions)} resolutions for video")
            return resolutions
            
        except Exception as e:
            logger.error(f"Failed to get video resolutions for URL {video_url}: {e}")
            return []
    
    def download_video_to_buffer(self, url: str, selected_resolution: str) -> Optional[BinaryIO]:
        """
        Download a YouTube video in the specified resolution and merge with audio.
        
        Args:
            url (str): The YouTube video URL
            selected_resolution (str): Resolution to download
            
        Returns:
            BinaryIO: Buffer containing the merged video or None if failed
        """
        try:
            logger.info(f"Starting video download for {url} at resolution {selected_resolution}")
            
            yt = YouTube(url, on_progress_callback=on_progress)
            
            # Get video and audio streams
            video_stream = yt.streams.filter(
                res=selected_resolution, progressive=False, file_extension="mp4"
            ).first()
            
            audio_stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()
            
            if not video_stream or not audio_stream:
                logger.error("Video or audio streams not found")
                return None
            
            # Step 1: Save both streams to temp files
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_temp:
                video_temp_path = video_temp.name
                video_stream.stream_to_buffer(video_temp)
                video_temp.flush()
            
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as audio_temp:
                audio_temp_path = audio_temp.name
                audio_stream.stream_to_buffer(audio_temp)
                audio_temp.flush()

            # Step 2: Merge video and audio streams using ffmpeg
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_temp:
                output_temp_path = output_temp.name

            video_input = ffmpeg.input(video_temp_path)
            audio_input = ffmpeg.input(audio_temp_path)

            ffmpeg.output(
                video_input, audio_input, output_temp_path, c="copy", loglevel="quiet"
            ).run(overwrite_output=True)

            # Step 3: Load merged file into buffer
            video_buffer = io.BytesIO()
            with open(output_temp_path, "rb") as f:
                video_buffer.write(f.read())
            video_buffer.seek(0)
            
            logger.info("Video download and merge completed successfully")
            
            # Step 4: Clean up temporary files
            try:
                os.remove(video_temp_path)
                os.remove(audio_temp_path)
                os.remove(output_temp_path)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up temp files: {cleanup_error}")
                
            return video_buffer

        except ffmpeg.Error as e:
            stderr = e.stderr.decode(errors="ignore") if e.stderr else "No stderr"
            stdout = e.stdout.decode(errors="ignore") if e.stdout else "No stdout"
            
            logger.error(f"[FFmpeg Error] STDERR: {stderr}, STDOUT: {stdout}")
            logger.error(f"Video download/merge failed for URL {url}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"General failure during video download for URL {url}: {e}")
            return None
    
    def download_audio_to_buffer(self, url: str) -> Optional[BinaryIO]:
        """
        Download audio from YouTube and convert to MP3.
        
        Args:
            url (str): The YouTube video URL
            
        Returns:
            BinaryIO: Buffer containing the MP3 audio or None if failed
        """
        try:
            logger.info(f"Starting audio download for {url}")
            
            yt = YouTube(url, on_progress_callback=on_progress)
            
            # Get audio stream
            audio_stream = (
                yt.streams.filter(only_audio=True, file_extension="mp4")
                .order_by("abr")
                .desc()
                .first()
            )
            
            if not audio_stream:
                logger.error("Audio stream not found")
                return None

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
                ffmpeg.input(temp_input_path)
                .output(
                    temp_output_path,
                    format="mp3",
                    acodec="libmp3lame",
                    audio_bitrate="192k",
                    ar="44100",
                    loglevel="quiet",
                )
                .run(overwrite_output=True)
            )

            # Step 4: Load converted audio into memory buffer
            mp3_buffer = io.BytesIO()
            with open(temp_output_path, "rb") as f:
                mp3_buffer.write(f.read())
            mp3_buffer.seek(0)
            
            logger.info("Audio download and conversion completed successfully")
            
            # Step 5: Cleanup temp files
            try:
                os.remove(temp_input_path)
                os.remove(temp_output_path)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up temp files: {cleanup_error}")
                
            return mp3_buffer

        except Exception as e:
            logger.error(f"Audio conversion failed for URL {url}: {e}")
            return None