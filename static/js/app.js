function onButtonClick() {
    alert("Your Video Has Started Download! Please don't close the current tab.")
}

const button = document.getElementById('download_btn_func');

button.addEventListener('click', onButtonClick);