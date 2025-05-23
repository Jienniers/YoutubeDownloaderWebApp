
# Youtube Video Downloader Web App

A Web App for downloading youtube videos at your favourite resolution.

### ⚖️ Legal Disclaimer

> 🚫 **This project is intended for educational and personal use only.**
>
> Downloading videos or audio from **YouTube** using this tool may violate [YouTube’s Terms of Service](https://www.youtube.com/t/terms) and/or **copyright laws**.
>
> The developer of this project does **not** support or encourage the downloading of copyrighted content from YouTube without permission from the content owner.
>
> This tool is provided **as-is**, with **no warranty** of any kind. Use it **at your own risk**.
>
> By using this project, you agree to take full responsibility for how you use it and to comply with all applicable laws and platform policies.

> 📌 **Note:** This project is **not affiliated with**, **endorsed by**, or **sponsored by YouTube** or Google Inc.


## Note
All this guide is for **windows**, I have not tested this web app on any other operating system so I don't know how it will work on there.

## Installation

Make sure to have python installed to run this program you can install it from [here](https://www.python.org/downloads/). You also need to have ffmeg installed on your pc, you can download it from [here](https://ffmpeg.org/download.html). you also need to have ffmeg in your environment variables.

The Program installs all the modules it self though if it doesn't install you can manually install them by using this command: 

```bash
  pip install flask pytubefix ffmpeg-python
```
After that you can open command line interface in the directly where this program and its files are located and run this command:
```bash
  python app.py
```
After running the program and everything is running fine, you need to open your browser and type in this url: ``` http://localhost:5000/ ```

**Note:** After the program has finished installing pytubefix by itself it might not work and give ImportError you just need to re run the program to fix it or manually first install all the packages before running the program.

**Note:** To get a alert that your video/audio has started downloading you must enable javascript in your browser though its optional but is recomended. Makesure to click "Ok" on the alert for the download to start.

    
## Authors

- [@Jienniers](https://github.com/Jienniers)


## Tech Stack

**Frontend:** HTML, CSS, JS

**Backend:** Flask

## Screenshots
#### Desktop Screenshots

![App Screenshot](https://github.com/Jienniers/YoutubeDownloaderWebApp/blob/main/screenshots/Screenshot1.png)

![App Screenshot](https://github.com/Jienniers/YoutubeDownloaderWebApp/blob/main/screenshots/Screenshot2.png)

#### Mobile Screenshots

![App Screenshot](https://github.com/Jienniers/YoutubeDownloaderWebApp/blob/main/screenshots/mobileScreenshot.png)

## Support

If you encounter any issues or have suggestions for improvement, please submit an issue on the GitHub repository.

