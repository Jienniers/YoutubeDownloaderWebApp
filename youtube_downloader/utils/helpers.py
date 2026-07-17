"""
Helper functions for YouTube Downloader.

This module contains utility functions that assist with 
various operations throughout the application.
"""

def format_video_length(video_length: int) -> str:
    """
    Format video length in seconds to MM:SS format.
    
    Args:
        video_length (int): Video length in seconds
        
    Returns:
        str: Formatted time string "MM:SS"
    """
    if not isinstance(video_length, int):
        return "00:00"
        
    minutes = video_length // 60
    seconds = video_length % 60
    
    formatted_length = f"{minutes:02}:{seconds:02}"
    return formatted_length