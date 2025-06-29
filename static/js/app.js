// Button Action For Video Download Button
const videoDownloadButton = document.getElementById('video_download_btn');

videoDownloadButton.addEventListener('click', function () {
    alert(
        "Your video download will begin shortly after clicking OK.\n\n" +
        "⚠️ Please keep this tab open while the download is in progress.\n\n" +
        "⏳ If you're downloading a long or high-quality video, it may take some time. The process runs in the background, so please be patient — your download will start automatically once it's ready."
    );
});


// Button Action For Audio Download Button
const audioDownloadButton = document.getElementById('audio_download_btn');

audioDownloadButton.addEventListener('click', function () {
    alert(
        "Your audio download will begin shortly after clicking OK.\n\n" +
        "🎵 Please keep this tab open while the download is in progress.\n\n" +
        "⏳ It may take a moment depending on the audio quality and length. Your download will start automatically once it's ready."
    );
});