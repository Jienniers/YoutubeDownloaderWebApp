"""
Custom exceptions for YouTube Downloader.

This module defines custom exception classes used throughout 
the application to provide more specific error handling.
"""

class DownloadError(Exception):
    """Exception raised when a download operation fails."""
    
    def __init__(self, message: str = "Download failed"):
        self.message = message
        super().__init__(self.message)

class ConversionError(Exception):
    """Exception raised when a conversion operation fails."""
    
    def __init__(self, message: str = "Conversion failed"):
        self.message = message
        super().__init__(self.message)