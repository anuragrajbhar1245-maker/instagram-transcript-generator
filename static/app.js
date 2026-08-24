// Instagram Transcript Generator Frontend Logic (Link + Upload + Universal Multilingual)

let currentTaskData = null;
let timerInterval = null;
let startTime = null;
let supportedLanguages = [];
let selectedFile = null;

// DOM Elements
const modeLinkBtn = document.getElementById("modeLinkBtn");
const modeUploadBtn = document.getElementById("modeUploadBtn");
const transcribeForm = document.getElementById("transcribeForm");
const uploadForm = document.getElementById("uploadForm");

const urlInput = document.getElementById("urlInput");
const pasteBtn = document.getElementById("pasteBtn");
const clearBtn = document.getElementById("clearBtn");
const submitBtn = document.getElementById("submitBtn");
const translateToEnglishCheckbox = document.getElementById("translateToEnglishCheckbox");
const quickLanguageSelect = document.getElementById("quickLanguageSelect");

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const selectedFileName = document.getElementById("selectedFileName");
const uploadTranslateCheckbox = document.getElementById("uploadTranslateCheckbox");
const uploadSubmitBtn = document.getElementById("uploadSubmitBtn");

const progressSection = document.getElementById("progressSection");
const progressStatusTitle = document.getElementById("progressStatusTitle");
const progressStatusDesc = document.getElementById("progressStatusDesc");
const elapsedTimer = document.getElementById("elapsedTimer");
const errorAlert = document.getElementById("errorAlert");
const errorMessage = document.getElementById("errorMessage");

const resultsSection = document.getElementById("resultsSection");
const reelThumbnail = document.getElementById("reelThumbnail");
const reelAuthor = document.getElementById("reelAuthor");
const reelTitle = document.getElementById("reelTitle");
const reelLink = document.getElementById("reelLink");
const langBadge = document.getElementById("langBadge");
const targetLangBadge = document.getElementById("targetLangBadge");
const durationBadge = document.getElementById("durationBadge");

const audioElement = document.getElementById("audioElement");
const audioCurrentTime = document.getElementById("audioCurrentTime");
const audioTotalDuration = document.getElementById("audioTotalDuration");
const playbackSpeed = document.getElementById("playbackSpeed");

const viewTimeline = document.getElementById("viewTimeline");
const viewText = document.getElementById("viewText");
const viewSummary = document.getElementById("viewSummary");
const viewRaw = document.getElementById("viewRaw");
const summaryParagraph = document.getElementById("summaryParagraph");
const keyPointsList = document.getElementById("keyPointsList");
const rawSubtitleCode = document.getElementById("rawSubtitleCode");

const searchInput = document.getElementById("searchTranscriptInput");
const copyTranscriptBtn = document.getElementById("copyTranscriptBtn");
const copyBtnText = document.getElementById("copyBtnText");

const exportDropdownBtn = document.getElementById("exportDropdownBtn");
const exportMenu = document.getElementById("exportMenu");

const instantTranslateSelect = document.getElementById("instantTranslateSelect");
const instantTranslateBtn = document.getElementById("instantTranslateBtn");

const settingsBtn = document.getElementById("settingsBtn");
const settingsModal = document.getElementById("settingsModal");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const modelSelect = document.getElementById("modelSelect");
const languageSelect = document.getElementById("languageSelect");
const engineSelect = document.getElementById("engineSelect");
const apiKeyInput = document.getElementById("apiKeyInput");
const cookiesInput = document.getElementById("cookiesInput");

const historyBtn = document.getElementById("historyBtn");
const historyModal = document.getElementById("historyModal");
const closeHistoryBtn = document.getElementById("closeHistoryBtn");
const historyList = document.getElementById("historyList");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");

// Mode Switching (Link vs Upload)
modeLinkBtn.addEventListener("click", () => {
  modeLinkBtn.classList.add("bg-rose-600", "text-white");
  modeLinkBtn.classList.remove("text-slate-400");
  modeUploadBtn.classList.remove("bg-rose-600", "text-white");
  modeUploadBtn.classList.add("text-slate-400");
  transcribeForm.classList.remove("hidden");
  uploadForm.classList.add("hidden");
});

modeUploadBtn.addEventListener("click", () => {
  modeUploadBtn.classList.add("bg-rose-600", "text-white");
  modeUploadBtn.classList.remove("text-slate-400");
  modeLinkBtn.classList.remove("bg-rose-600", "text-white");
  modeLinkBtn.classList.add("text-slate-400");
  uploadForm.classList.remove("hidden");
  transcribeForm.classList.add("hidden");
});

// File Drag and Drop Handlers
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("border-rose-500", "bg-slate-800/60");
});
dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("border-rose-500", "bg-slate-800/60");
});
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("border-rose-500", "bg-slate-800/60");
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    handleFileSelected(e.dataTransfer.files[0]);
  }
});
fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files[0]) {
    handleFileSelected(e.target.files[0]);
  }
});

function handleFileSelected(file) {
  selectedFile = file;
  selectedFileName.textContent = `Selected: ${file.name} (${Math.round(file.size / 1024 / 1024 * 10) / 10} MB)`;
  selectedFileName.classList.remove("hidden");
  uploadSubmitBtn.disabled = false;
  uploadSubmitBtn.classList.remove("opacity-50", "cursor-not-allowed");
}

// Upload Form Submission
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedFile) return;

  errorAlert.classList.add("hidden");
  resultsSection.classList.add("hidden");
  progressSection.classList.remove("hidden");
  uploadSubmitBtn.disabled = true;

  startTimer();
  updateStep(1);
  progressStatusTitle.textContent = "Uploading & Converting Media...";

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("model_size", localStorage.getItem("insta_model") || "tiny");
  formData.append("engine", localStorage.getItem("insta_engine") || "local");
  formData.append("api_key", localStorage.getItem("insta_api_key") || "");
  formData.append("language", quickLanguageSelect.value || "auto");
  formData.append("task", uploadTranslateCheckbox.checked ? "translate" : "transcribe");

  try {
    setTimeout(() => updateStep(2), 2000);

    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Upload error: ${response.status}`);
    }

    const data = await response.json();
    updateStep(3);

    setTimeout(() => {
      stopTimer();
      progressSection.classList.add("hidden");
      renderResults(data);
      saveToHistory(data);
      uploadSubmitBtn.disabled = false;
    }, 600);

  } catch (err) {
    stopTimer();
    progressSection.classList.add("hidden");
    uploadSubmitBtn.disabled = false;
    errorMessage.textContent = err.message || "Failed to process the uploaded file.";
    errorAlert.classList.remove("hidden");
  }
});

// Fetch supported languages and populate dropdowns
async function fetchLanguages() {
  try {
    const res = await fetch("/api/languages");
    if (res.ok) {
      supportedLanguages = await res.json();
      populateLanguageDropdowns();
    }
  } catch (err) {
    console.error("Failed to load languages:", err);
  }
}

function populateLanguageDropdowns() {
  quickLanguageSelect.innerHTML = "";
  languageSelect.innerHTML = "";
  instantTranslateSelect.innerHTML = `<option value="" disabled selected>Translate into...</option>`;

  supportedLanguages.forEach(lang => {
    const opt1 = document.createElement("option");
    opt1.value = lang.code;
    opt1.textContent = lang.name;
    quickLanguageSelect.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = lang.code;
    opt2.textContent = lang.name;
    languageSelect.appendChild(opt2);

    if (lang.code !== "auto") {
      const opt3 = document.createElement("option");
      opt3.value = lang.code;
      opt3.textContent = lang.name;
      instantTranslateSelect.appendChild(opt3);
    }
  });

  const savedLang = localStorage.getItem("insta_lang") || "auto";
  quickLanguageSelect.value = savedLang;
  languageSelect.value = savedLang;
}

// Settings initialization from LocalStorage
function loadSettings() {
  const savedModel = localStorage.getItem("insta_model") || "tiny";
  const savedLang = localStorage.getItem("insta_lang") || "auto";
  const savedEngine = localStorage.getItem("insta_engine") || "local";
  const savedApiKey = localStorage.getItem("insta_api_key") || "";
  const savedCookies = localStorage.getItem("insta_cookies") || "";

  modelSelect.value = savedModel;
  languageSelect.value = savedLang;
  engineSelect.value = savedEngine;
  apiKeyInput.value = savedApiKey;
  if (cookiesInput) cookiesInput.value = savedCookies;
}

function saveSettings() {
  localStorage.setItem("insta_model", modelSelect.value);
  localStorage.setItem("insta_lang", languageSelect.value);
  localStorage.setItem("insta_engine", engineSelect.value);
  localStorage.setItem("insta_api_key", apiKeyInput.value.trim());
  if (cookiesInput) localStorage.setItem("insta_cookies", cookiesInput.value.trim());
  quickLanguageSelect.value = languageSelect.value;
  settingsModal.classList.add("hidden");
}

// History Management
function saveToHistory(item) {
  let history = JSON.parse(localStorage.getItem("insta_history") || "[]");
  history = history.filter(h => h.task_id !== item.task_id);
  history.unshift({
    task_id: item.task_id,
    title: item.metadata.title,
    uploader: item.metadata.uploader,
    thumbnail: item.metadata.thumbnail,
    duration: item.metadata.duration_formatted,
    timestamp: new Date().toISOString(),
    data: item
  });
  if (history.length > 20) history.pop();
  localStorage.setItem("insta_history", JSON.stringify(history));
}

function renderHistory() {
  const history = JSON.parse(localStorage.getItem("insta_history") || "[]");
  historyList.innerHTML = "";

  if (history.length === 0) {
    historyList.innerHTML = `<p class="text-slate-500 text-center py-4">No recent transcripts found.</p>`;
    return;
  }

  history.forEach(item => {
    const el = document.createElement("div");
    el.className = "p-2.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-white/5 cursor-pointer flex items-center justify-between transition-colors";
    el.innerHTML = `
      <div class="flex items-center gap-2.5 overflow-hidden">
        <img src="${item.thumbnail || ''}" onerror="this.style.display='none'" class="w-9 h-11 object-cover rounded bg-slate-900 flex-shrink-0">
        <div class="truncate">
          <p class="font-medium text-slate-200 truncate">${item.title || 'Instagram Reel'}</p>
          <p class="text-[11px] text-slate-400">@${item.uploader} • ${item.duration}</p>
        </div>
      </div>
      <button class="px-2 py-1 text-[11px] bg-rose-600/30 text-rose-300 rounded hover:bg-rose-600/50 flex-shrink-0 ml-2">Load</button>
    `;
    el.onclick = () => {
      renderResults(item.data);
      historyModal.classList.add("hidden");
    };
    historyList.appendChild(el);
  });
}

// Input Helpers
urlInput.addEventListener("input", () => {
  clearBtn.classList.toggle("hidden", !urlInput.value);
});

clearBtn.addEventListener("click", () => {
  urlInput.value = "";
  clearBtn.classList.add("hidden");
  urlInput.focus();
});

pasteBtn.addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      urlInput.value = text;
      clearBtn.classList.remove("hidden");
      urlInput.focus();
    }
  } catch (err) {
    console.error("Clipboard access failed:", err);
  }
});

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// URL Form Submission
transcribeForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  errorAlert.classList.add("hidden");
  resultsSection.classList.add("hidden");
  progressSection.classList.remove("hidden");
  submitBtn.disabled = true;
  submitBtn.classList.add("opacity-70");

  startTimer();
  updateStep(1);

  const isTranslateToEnglish = translateToEnglishCheckbox.checked;
  const chosenLang = quickLanguageSelect.value;

  const payload = {
    url: url,
    model_size: localStorage.getItem("insta_model") || "tiny",
    engine: localStorage.getItem("insta_engine") || "local",
    api_key: localStorage.getItem("insta_api_key") || null,
    cookies: localStorage.getItem("insta_cookies") || null,
    language: chosenLang,
    task: isTranslateToEnglish ? "translate" : "transcribe"
  };

  try {
    setTimeout(() => updateStep(2), 2500);

    const response = await fetch("/api/transcribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error: ${response.status}`);
    }

    const data = await response.json();
    updateStep(3);

    setTimeout(() => {
      stopTimer();
      progressSection.classList.add("hidden");
      renderResults(data);
      saveToHistory(data);
      submitBtn.disabled = false;
      submitBtn.classList.remove("opacity-70");
    }, 600);

  } catch (err) {
    stopTimer();
    progressSection.classList.add("hidden");
    submitBtn.disabled = false;
    submitBtn.classList.remove("opacity-70");
    errorMessage.textContent = err.message || "Failed to process the Instagram link.";
    errorAlert.classList.remove("hidden");
  }
});

function updateStep(step) {
  const step1 = document.getElementById("step1");
  const step2 = document.getElementById("step2");
  const step3 = document.getElementById("step3");

  [step1, step2, step3].forEach(s => s.classList.remove("bg-rose-500/20", "border-rose-500/50", "text-rose-200"));

  if (step === 1) {
    step1.classList.add("bg-rose-500/20", "border-rose-500/50", "text-rose-200");
    progressStatusTitle.textContent = "Extracting Audio...";
    progressStatusDesc.textContent = "Downloading and converting high-definition audio track";
  } else if (step === 2) {
    step2.classList.add("bg-rose-500/20", "border-rose-500/50", "text-rose-200");
    progressStatusTitle.textContent = "Transcribing with Whisper AI...";
    progressStatusDesc.textContent = "Detecting speech and generating timestamped segments";
  } else if (step === 3) {
    step3.classList.add("bg-rose-500/20", "border-rose-500/50", "text-rose-200");
    progressStatusTitle.textContent = "Formatting & Translating...";
    progressStatusDesc.textContent = "Preparing interactive subtitles and summary";
  }
}

function startTimer() {
  startTime = Date.now();
  elapsedTimer.textContent = "00:00";
  timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    elapsedTimer.textContent = formatTime(elapsed);
  }, 1000);
}

function stopTimer() {
  if (timerInterval) clearInterval(timerInterval);
}

// On-The-Fly Translation Action
instantTranslateBtn.addEventListener("click", async () => {
  if (!currentTaskData) return;
  const targetLang = instantTranslateSelect.value;
  if (!targetLang) return;

  instantTranslateBtn.disabled = true;
  instantTranslateBtn.innerHTML = `<i class="ph-bold ph-spinner animate-spin"></i>`;

  try {
    const response = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_id: currentTaskData.task_id,
        target_language: targetLang
      })
    });

    if (!response.ok) {
      throw new Error("Translation failed.");
    }

    const transData = await response.json();
    currentTaskData.transcription.translated_segments = transData.translated_segments;
    currentTaskData.transcription.translated_full_text = transData.translated_full_text;
    currentTaskData.transcription.target_language = transData.target_language;
    currentTaskData.transcription.target_language_name = transData.target_language_name;
    currentTaskData.summary = transData.summary;
    currentTaskData.formats = transData.formats;

    renderResults(currentTaskData);
  } catch (err) {
    alert("Could not translate transcript: " + err.message);
  } finally {
    instantTranslateBtn.disabled = false;
    instantTranslateBtn.textContent = "Go";
  }
});

// Render Results
function renderResults(data) {
  currentTaskData = data;
  const meta = data.metadata || {};
  const trans = data.transcription || {};
  const activeSegments = trans.translated_segments || trans.segments || [];

  reelThumbnail.src = meta.thumbnail || "";
  reelThumbnail.onerror = () => { reelThumbnail.style.display = "none"; };
  reelAuthor.textContent = meta.uploader ? `@${meta.uploader}` : "@creator";
  reelTitle.textContent = meta.title || meta.description || "Instagram Video";
  
  if (meta.webpage_url) {
    reelLink.href = meta.webpage_url;
    reelLink.style.display = "inline-flex";
  } else {
    reelLink.style.display = "none";
  }

  durationBadge.textContent = meta.duration_formatted || formatTime(trans.duration || 0);

  const lang = (trans.detected_language || "auto").toUpperCase();
  const langName = trans.language_name || lang;
  const langProb = trans.language_probability ? ` (${Math.round(trans.language_probability * 100)}%)` : "";
  langBadge.textContent = `${langName}${langProb}`;

  if (trans.target_language) {
    targetLangBadge.textContent = `→ ${trans.target_language_name || trans.target_language.toUpperCase()}`;
    targetLangBadge.classList.remove("hidden");
  } else if (trans.task === "translate") {
    targetLangBadge.textContent = `→ English (Direct)`;
    targetLangBadge.classList.remove("hidden");
  } else {
    targetLangBadge.classList.add("hidden");
  }

  audioElement.src = data.audio_url || `/api/audio/${data.task_id}`;
  audioElement.controls = true;

  viewTimeline.innerHTML = "";
  if (activeSegments.length === 0) {
    viewTimeline.innerHTML = `<p class="text-slate-400 text-center py-6">No speech detected in this audio.</p>`;
  } else {
    activeSegments.forEach((seg) => {
      const segEl = document.createElement("div");
      segEl.className = "segment-item group p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/5 flex items-start gap-3 transition-all cursor-pointer";
      segEl.dataset.start = seg.start;
      segEl.dataset.end = seg.end;

      const startTimeStr = formatTime(seg.start);
      const originalSubtext = seg.original_text && seg.original_text !== seg.text 
        ? `<p class="text-xs text-slate-500 mt-1 italic">${seg.original_text}</p>` 
        : "";

      segEl.innerHTML = `
        <button class="seek-btn px-2 py-1 rounded bg-slate-800 group-hover:bg-rose-600/30 text-slate-300 group-hover:text-rose-300 font-mono text-xs flex-shrink-0 transition-colors flex items-center gap-1">
          <i class="ph-bold ph-play text-[10px]"></i>
          <span>${startTimeStr}</span>
        </button>
        <div class="flex-1">
          <p class="seg-text text-sm text-slate-200 leading-relaxed">${seg.text}</p>
          ${originalSubtext}
        </div>
      `;

      segEl.onclick = () => {
        audioElement.currentTime = seg.start;
        audioElement.play();
      };

      viewTimeline.appendChild(segEl);
    });
  }

  viewText.textContent = trans.translated_full_text || trans.full_text || "No transcription text available.";

  const summary = data.summary || {};
  summaryParagraph.textContent = summary.summary || "No summary generated.";
  keyPointsList.innerHTML = "";
  if (summary.key_points && summary.key_points.length > 0) {
    summary.key_points.forEach(pt => {
      const li = document.createElement("li");
      li.className = "flex items-start gap-2 text-slate-300";
      li.innerHTML = `<i class="ph-bold ph-check text-emerald-400 mt-1 flex-shrink-0"></i><span>${pt.replace(/^[•\-\*]\s*/, '')}</span>`;
      keyPointsList.appendChild(li);
    });
  } else {
    keyPointsList.innerHTML = `<li class="text-slate-500">No key points extracted.</li>`;
  }

  rawSubtitleCode.textContent = data.formats?.srt || "";

  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth" });
}

// Audio Player Time Synchronizer
audioElement.addEventListener("timeupdate", () => {
  const cur = audioElement.currentTime;
  const dur = audioElement.duration || 0;
  audioCurrentTime.textContent = formatTime(cur);
  audioTotalDuration.textContent = formatTime(dur);

  const segEls = document.querySelectorAll(".segment-item");
  segEls.forEach(el => {
    const start = parseFloat(el.dataset.start);
    const end = parseFloat(el.dataset.end);
    if (cur >= start && cur <= end) {
      el.classList.add("segment-active");
    } else {
      el.classList.remove("segment-active");
    }
  });
});

playbackSpeed.addEventListener("change", (e) => {
  audioElement.playbackRate = parseFloat(e.target.value);
});

// Search & Highlight Filter
searchInput.addEventListener("input", (e) => {
  const query = e.target.value.toLowerCase().trim();
  const segEls = document.querySelectorAll(".segment-item");

  segEls.forEach(el => {
    const textEl = el.querySelector(".seg-text");
    const rawText = textEl.textContent;
    if (!query) {
      el.classList.remove("hidden");
      textEl.innerHTML = rawText;
      return;
    }

    if (rawText.toLowerCase().includes(query)) {
      el.classList.remove("hidden");
      const regex = new RegExp(`(${query})`, "gi");
      textEl.innerHTML = rawText.replace(regex, `<span class="search-highlight">$1</span>`);
    } else {
      el.classList.add("hidden");
    }
  });
});

// Tabs Switching
const tabButtons = {
  tabTimeline: { btn: document.getElementById("tabTimeline"), view: viewTimeline },
  tabText: { btn: document.getElementById("tabText"), view: viewText },
  tabSummary: { btn: document.getElementById("tabSummary"), view: viewSummary },
  tabRaw: { btn: document.getElementById("tabRaw"), view: viewRaw },
};

Object.keys(tabButtons).forEach(key => {
  const item = tabButtons[key];
  item.btn.addEventListener("click", () => {
    Object.values(tabButtons).forEach(t => {
      t.btn.classList.remove("text-white", "bg-slate-800");
      t.btn.classList.add("text-slate-400");
      t.view.classList.add("hidden");
    });
    item.btn.classList.add("text-white", "bg-slate-800");
    item.btn.classList.remove("text-slate-400");
    item.view.classList.remove("hidden");
  });
});

// Copy to Clipboard
copyTranscriptBtn.addEventListener("click", async () => {
  if (!currentTaskData) return;
  const activeTab = document.querySelector(".tab-btn.bg-slate-800");
  let textToCopy = "";

  if (activeTab && activeTab.id === "tabTimeline") {
    textToCopy = currentTaskData.formats?.txt || "";
  } else if (activeTab && activeTab.id === "tabText") {
    textToCopy = currentTaskData.transcription?.translated_full_text || currentTaskData.transcription?.full_text || "";
  } else if (activeTab && activeTab.id === "tabSummary") {
    textToCopy = currentTaskData.summary?.summary || "";
  } else {
    textToCopy = currentTaskData.formats?.srt || "";
  }

  await navigator.clipboard.writeText(textToCopy);
  copyBtnText.textContent = "Copied!";
  setTimeout(() => { copyBtnText.textContent = "Copy"; }, 2000);
});

// Export Dropdown
exportDropdownBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  exportMenu.classList.toggle("hidden");
});

document.addEventListener("click", () => {
  exportMenu.classList.add("hidden");
});

function downloadExport(format) {
  if (!currentTaskData) return;
  const taskId = currentTaskData.task_id;
  window.location.href = `/api/export/${taskId}/${format}`;
  exportMenu.classList.add("hidden");
}

// Settings Modal
settingsBtn.addEventListener("click", () => {
  loadSettings();
  settingsModal.classList.remove("hidden");
});
closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));
saveSettingsBtn.addEventListener("click", saveSettings);

// History Modal
historyBtn.addEventListener("click", () => {
  renderHistory();
  historyModal.classList.remove("hidden");
});
closeHistoryBtn.addEventListener("click", () => historyModal.classList.add("hidden"));
clearHistoryBtn.addEventListener("click", () => {
  localStorage.removeItem("insta_history");
  renderHistory();
});

// Initialize on page load
loadSettings();
fetchLanguages();
