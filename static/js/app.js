// Button Action For Video Download Button
const videoDownloadButton = document.getElementById('video_download_btn_func');

videoDownloadButton.addEventListener('click', function () {
    alert("Your video will start downloading once you click the Ok button on this alert. Please don't close the current tab.");
});

// Button Action For Audio Download Button
const audioDownloadButton = document.getElementById('audio_download_btn_func');

audioDownloadButton.addEventListener('click', function () {
    alert("Your audio will start downloading once you click the Ok button on this alert. Please don't close the current tab.");
});
