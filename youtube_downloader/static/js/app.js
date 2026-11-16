const videoDownloadButton = document.getElementById("video_download_btn");
const queuePanel = document.getElementById("download-queue");
const queueItems = document.getElementById("queue-items");
const queueCount = document.getElementById("queue-count");
const progressPanel = document.getElementById("download-progress");
const progressFill = document.getElementById("progress-fill");
const progressValue = document.getElementById("progress-value");
const progressLabel = document.getElementById("progress-label");
const progressNote = document.getElementById("progress-note");
let queue = [];
let processing = false;
let currentUrl = document.getElementById("main-form")?.dataset.currentUrl || "";
let activeJobId = null;

document.getElementById("in-between")?.addEventListener("click", async event => {
  event.preventDefault();
  const input = document.getElementById("url_link");
  const url = input.value.trim();
  if (!url) return;
  const button = event.currentTarget;
  const oldLabel = button.textContent;
  button.disabled = true;
  button.textContent = "Searching…";
  try {
    const response = await fetch("/api/video-info", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not find that video.");
    currentUrl = url;
    document.getElementById("main-form").dataset.currentUrl = url;
    document.querySelector("h2").textContent = data.title;
    const image = document.getElementById("video-thumbnail");
    image.src = data.thumbnail;
    image.classList.remove("hidden");
    const select = document.getElementById("resolutions");
    select.replaceChildren(...data.resolutions.map(resolution => {
      const option = document.createElement("option");
      option.value = resolution;
      option.textContent = resolution;
      return option;
    }));
    select.style.visibility = "visible";
    document.getElementById("video_download_btn").style.visibility = "visible";
    document.getElementById("audio_download_btn").style.visibility = "visible";
    document.querySelector("[data-video-length]").textContent = `Video Length: ${data.length}`;
    document.querySelector("[data-video-length]").closest("div").style.visibility = "visible";
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
    button.textContent = oldLabel;
  }
});

function renderQueue() {
  const waiting = queue.filter(item => !item.active);
  queuePanel.classList.toggle("hidden", waiting.length === 0);
  queueCount.textContent = `${waiting.length} ${waiting.length === 1 ? "video" : "videos"}`;
  queueItems.replaceChildren();
  waiting.forEach(item => {
    const row = document.createElement("button");
    row.type = "button";
    row.setAttribute("role", "option");
    row.setAttribute("aria-selected", String(Boolean(item.selected)));
    row.className = `w-full rounded-lg border px-3 py-3 text-left transition-colors ${item.selected ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40" : "border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 hover:border-blue-300"} cursor-pointer`;
    const title = document.createElement("span");
    title.className = "block truncate font-medium text-gray-800 dark:text-zinc-100";
    title.textContent = item.title || item.url;
    const detail = document.createElement("span");
    detail.className = "mt-1 block text-xs text-gray-500 dark:text-zinc-400";
    detail.textContent = `${item.resolution} · Waiting in queue`;
    row.append(title, detail);
    row.addEventListener("click", () => { item.selected = !item.selected; renderQueue(); });
    queueItems.append(row);
  });
}

function setProgress(percent, title) {
  progressPanel.classList.remove("hidden");
  progressFill.style.width = `${percent}%`;
  progressFill.setAttribute("aria-valuenow", String(percent));
  progressValue.textContent = `${percent}%`;
  progressLabel.textContent = title ? `Preparing ${title}` : "Preparing video…";
}

async function runQueue() {
  if (processing) return;
  processing = true;
  try {
    while (queue.length) {
      const item = queue[0];
      item.active = true;
      renderQueue();
      setProgress(0, item.title);
      progressNote.textContent = "Getting the video ready. Your download will begin when processing is complete.";
      const start = await fetch("/api/video-download", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: item.url, resolution: item.resolution }),
      });
      if (!start.ok) throw new Error("Could not start video processing.");
      const { jobId } = await start.json();
      activeJobId = jobId;
      document.getElementById("cancel-download").disabled = false;
      let status;
      do {
        await new Promise(resolve => setTimeout(resolve, 650));
        const response = await fetch(`/api/video-download/${jobId}`);
        if (!response.ok) throw new Error("Could not read processing status.");
        status = await response.json();
        setProgress(status.progress || 0, status.title || item.title);
        if (status.status === "error") throw new Error(status.error || "Video processing failed.");
      } while (!["complete", "cancelled"].includes(status.status));
      if (status.status === "cancelled") {
        activeJobId = null;
        const cancelButton = document.getElementById("cancel-download");
        cancelButton.disabled = false;
        cancelButton.textContent = "Cancel download";
        queue.shift();
        renderQueue();
        progressLabel.textContent = "Download cancelled";
        progressNote.textContent = "The video was cancelled. Remaining videos will continue in order.";
        await new Promise(resolve => setTimeout(resolve, 700));
        continue;
      }
      progressLabel.textContent = "Video ready";
      progressNote.textContent = "Starting your download…";
      const fileResponse = await fetch(`/api/video-download/${jobId}/file`);
      if (!fileResponse.ok) throw new Error("The processed video could not be downloaded.");
      const blob = await fileResponse.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = status.title ? `${status.title}.mp4` : "youtube-video.mp4";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
      queue.shift();
      activeJobId = null;
      document.getElementById("cancel-download").disabled = false;
      document.getElementById("cancel-download").textContent = "Cancel download";
      renderQueue();
      await new Promise(resolve => setTimeout(resolve, 700));
    }
    progressPanel.classList.add("hidden");
  } catch (error) {
    progressLabel.textContent = "Could not process this video";
    progressNote.textContent = error.message;
    if (queue.length) {
      queue[0].active = false;
      queue[0].selected = true;
      renderQueue();
    }
  } finally {
    processing = false;
    activeJobId = null;
    const cancelButton = document.getElementById("cancel-download");
    cancelButton.disabled = false;
    cancelButton.textContent = "Cancel download";
  }
}

document.getElementById("cancel-download")?.addEventListener("click", async event => {
  if (!activeJobId) return;
  const button = event.currentTarget;
  button.disabled = true;
  button.textContent = "Cancelling…";
  progressNote.textContent = "Stopping the current download…";
  try {
    const response = await fetch(`/api/video-download/${activeJobId}/cancel`, { method: "POST" });
    if (!response.ok && response.status !== 409) throw new Error("Could not cancel this download.");
  } catch (error) {
    progressNote.textContent = error.message;
    button.disabled = false;
    button.textContent = "Cancel download";
  }
});

videoDownloadButton?.addEventListener("click", event => {
  event.preventDefault();
  const url = currentUrl;
  const title = document.querySelector("h2")?.textContent.trim() || url;
  const resolution = document.getElementById("resolutions")?.value;
  if (!url || !resolution) return;
  queue.push({ url, title, resolution, selected: false, active: false });
  renderQueue();
  if (!processing) runQueue();
});

document.getElementById("delete-selected")?.addEventListener("click", () => {
  queue = queue.filter(item => !item.selected || item.active);
  renderQueue();
});

document.getElementById("clear-queue")?.addEventListener("click", () => {
  queue = queue.filter(item => item.active);
  renderQueue();
});

document.getElementById("audio_download_btn")?.addEventListener("click", () => {
  alert("Your audio download will begin shortly. Please keep this tab open while it is processing.");
});

const themeToggle = document.getElementById("theme-toggle");
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "dark" || (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
  document.documentElement.classList.add("dark");
}
themeToggle?.addEventListener("click", () => {
  document.documentElement.classList.toggle("dark");
  localStorage.setItem("theme", document.documentElement.classList.contains("dark") ? "dark" : "light");
});
