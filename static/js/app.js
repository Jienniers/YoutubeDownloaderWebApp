// Button Action For Video Download Button
function onVideoDownloadClick() {
    alert("Your Video Has Started Downloading! Please don't close the current tab.");
}

const videoDownloadButton = document.getElementById('video_download_btn_func');
videoDownloadButton.addEventListener('click', onVideoDownloadClick);

// Button Action For Audio Download Button
function onAudioDownloadClick() {
    alert("Your Audio Has Started Downloading! Please don't close the current tab.");
}

const audioDownloadButton = document.getElementById('audio_download_btn_func');
audioDownloadButton.addEventListener('click', onAudioDownloadClick);
