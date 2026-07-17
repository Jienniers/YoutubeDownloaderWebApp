from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="youtube-downloader",
    version="1.0.0",
    author="Jienniers",
    author_email="jienniers@example.com",
    description="A web application for downloading YouTube videos and audio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Jienniers/YoutubeDownloaderWebApp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "pytubefix",
        "flask", 
        "ffmpeg-python"
    ],
    entry_points={
        'console_scripts': [
            'youtube-downloader=app:main',
        ],
    },
)