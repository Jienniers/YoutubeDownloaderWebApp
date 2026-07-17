"""
Data model for YouTube video information.

This module defines the VideoInfo class that represents 
the metadata of a YouTube video.
"""

from dataclasses import dataclass


@dataclass
class VideoInfo:
    """Data class representing YouTube video information."""
    
    title: str
    thumbnail_url: str
    length: int  # Length in seconds
    
    def __post_init__(self):
        """Validate and process the data after initialization."""
        if not isinstance(self.length, int) or self.length < 0:
            raise ValueError("Length must be a non-negative integer")