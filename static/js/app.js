// Button Action For Video Download Button
const videoDownloadButton = document.getElementById("video_download_btn");

console.log("app.js loaded");

videoDownloadButton.addEventListener("click", function () {
  alert(
    "Your video download will begin shortly after clicking OK.\n\n" +
      "⚠️ Please keep this tab open while the download is in progress.\n\n" +
      "⏳ If you're downloading a long or high-quality video, it may take some time. The process runs in the background, so please be patient — your download will start automatically once it's ready.",
  );
});

// Button Action For Audio Download Button
const audioDownloadButton = document.getElementById("audio_download_btn");

audioDownloadButton.addEventListener("click", function () {
  alert(
    "Your audio download will begin shortly after clicking OK.\n\n" +
      "🎵 Please keep this tab open while the download is in progress.\n\n" +
      "⏳ It may take a moment depending on the audio quality and length. Your download will start automatically once it's ready.",
  );
});

const themeToggle = document.getElementById("theme-toggle");
const savedTheme = localStorage.getItem("theme");

// Initialize theme
if (
  savedTheme === "dark" ||
  (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)
) {
  document.documentElement.classList.add("dark");
}

// Toggle theme
themeToggle.addEventListener("click", () => {
  document.documentElement.classList.toggle("dark");

  localStorage.setItem(
    "theme",
    document.documentElement.classList.contains("dark") ? "dark" : "light",
  );
});
