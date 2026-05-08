/**
 * popup.js — PhishGuard Chrome Extension
 * Captures the active tab's URL and sends it to the Flask ML backend.
 */

const API_URL = "http://localhost:5000/predict";

/* ── DOM refs ───────────────────────────────────────── */
const urlDisplay      = document.getElementById("urlDisplay");
const resultCard      = document.getElementById("resultCard");
const scanState       = document.getElementById("scanState");
const resultState     = document.getElementById("resultState");
const errorState      = document.getElementById("errorState");
const errorText       = document.getElementById("errorText");
const statusIcon      = document.getElementById("statusIcon");
const statusIconWrap  = document.getElementById("statusIconWrap");
const verdict         = document.getElementById("verdict");
const verdictSub      = document.getElementById("verdictSub");
const confidenceValue = document.getElementById("confidenceValue");
const meterFill       = document.getElementById("meterFill");
const featureList     = document.getElementById("featureList");
const scanBtn         = document.getElementById("scanBtn");
const retryBtn        = document.getElementById("retryBtn");

/* ── State ──────────────────────────────────────────── */
let currentUrl = "";

/* ── Helpers ────────────────────────────────────────── */
function showState(state) {
  [scanState, resultState, errorState].forEach(el => el.classList.add("hidden"));
  state.classList.remove("hidden");
}

function clearResultClass() {
  resultCard.classList.remove("is-safe", "is-warn", "is-danger");
}

/**
 * Maps result label + confidence → UI configuration.
 * result: 'safe' | 'suspicious' | 'phishing'
 */
function getConfig(result, confidence) {
  if (result === "safe") {
    return {
      cls:     "is-safe",
      icon:    "✓",
      label:   "SAFE",
      sub:     "No phishing indicators detected",
    };
  }
  if (result === "suspicious" || (result === "phishing" && confidence < 70)) {
    return {
      cls:     "is-warn",
      icon:    "⚑",
      label:   "SUSPICIOUS",
      sub:     "Potentially deceptive URL — proceed with caution",
    };
  }
  return {
    cls:     "is-danger",
    icon:    "✕",
    label:   "PHISHING",
    sub:     "High-confidence phishing attempt detected",
  };
}

/** Render feature flags returned by the API */
function renderFeatures(features) {
  featureList.innerHTML = "";
  if (!features || !features.length) return;

  features.forEach(({ name, flagged }) => {
    const tag = document.createElement("span");
    tag.className = "feat-tag" + (flagged ? " flagged" : "");
    tag.textContent = name;
    featureList.appendChild(tag);
  });
}

/** Animate the confidence meter */
function animateMeter(pct) {
  // Force reflow so transition fires
  meterFill.style.width = "0%";
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      meterFill.style.width = `${pct}%`;
    });
  });
}

/* ── Core Analyse Function ──────────────────────────── */
async function analyseUrl(url) {
  clearResultClass();
  showState(scanState);
  scanBtn.disabled = true;

  try {
    const response = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url }),
    });

    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`);
    }

    const data = await response.json();
    // Expected: { result: 'phishing'|'suspicious'|'safe', confidence: 92.5, features: [...] }

    const { result, confidence, features } = data;
    const cfg = getConfig(result, confidence);

    resultCard.classList.add(cfg.cls);
    statusIcon.textContent = cfg.icon;
    verdict.textContent    = cfg.label;
    verdictSub.textContent = cfg.sub;
    confidenceValue.textContent = `${confidence.toFixed(1)}%`;

    animateMeter(confidence);
    renderFeatures(features || []);
    showState(resultState);

  } catch (err) {
    errorText.textContent =
      err.message.includes("Failed to fetch")
        ? "Cannot connect to the analysis server.\nMake sure the Flask API is running on localhost:5000."
        : err.message;
    showState(errorState);
  } finally {
    scanBtn.disabled = false;
  }
}

/* ── Get Active Tab URL ─────────────────────────────── */
async function getActiveTabUrl() {
  return new Promise((resolve, reject) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (chrome.runtime.lastError) return reject(chrome.runtime.lastError);
      if (!tabs || !tabs[0]) return reject(new Error("No active tab found"));
      resolve(tabs[0].url || "");
    });
  });
}

/* ── Init ───────────────────────────────────────────── */
async function init() {
  try {
    currentUrl = await getActiveTabUrl();
    urlDisplay.textContent = currentUrl || "No URL found";
  } catch {
    urlDisplay.textContent = "Could not read tab URL";
  }
}

/* ── Event Listeners ────────────────────────────────── */
scanBtn.addEventListener("click", () => {
  if (currentUrl) analyseUrl(currentUrl);
});

retryBtn.addEventListener("click", () => {
  if (currentUrl) analyseUrl(currentUrl);
});

/* ── Boot ───────────────────────────────────────────── */
init();
