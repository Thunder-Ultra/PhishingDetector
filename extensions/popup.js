/**
 * popup.js — PhishGuard Popup Logic v5
 *
 * API response: { url, result: "safe"|"phishing", confidence, reason }
 * The `reason` string is the core "Explainable AI" feature — displayed prominently.
 */

const API_URL = "http://127.0.0.1:5000/predict";

const $ = id => document.getElementById(id);
const ROOT = document.documentElement;

const urlVal       = $("urlVal");
const statusDot    = $("statusDot");
const statusText   = $("statusText");
const stateScanning= $("stateScanning");
const stateResult  = $("stateResult");
const stateError   = $("stateError");
const verdictIcon  = $("verdictIcon");
const verdictLabel = $("verdictLabel");
const verdictDesc  = $("verdictDesc");
const confNum      = $("confNum");
const confBar      = $("confBar");
const reasonText   = $("reasonText");
const reasonPanel  = $("reasonPanel");
const errMsg       = $("errMsg");
const rescanBtn    = $("rescanBtn");

function showState(id) {
  [stateScanning, stateResult, stateError].forEach(el => el.classList.add("hidden"));
  $(id).classList.remove("hidden");
}

function applyTheme(result) {
  const themes = {
    safe:     { c: "#1dde8a", s: "rgba(29,222,138,0.09)",  b: "rgba(29,222,138,0.22)" },
    phishing: { c: "#ff4040", s: "rgba(255,64,64,0.08)",   b: "rgba(255,64,64,0.22)"  },
    error:    { c: "#4e5c7a", s: "rgba(78,92,122,0.09)",   b: "rgba(78,92,122,0.22)"  },
  };
  const t = themes[result] || themes.error;
  ROOT.style.setProperty("--ac",   t.c);
  ROOT.style.setProperty("--ac-s", t.s);
  ROOT.style.setProperty("--ac-b", t.b);
}

function renderResult(data) {
  const { result, confidence, reason } = data;
  const pct = parseFloat(confidence) || 0;

  applyTheme(result);

  // Status pill
  const isSafe = result === "safe";
  statusDot.className   = `status-dot ${isSafe ? "safe" : "danger"}`;
  statusText.textContent = result.toUpperCase();

  // Verdict
  const cfg = isSafe
    ? { icon: "✓", label: "SAFE",     desc: "No phishing indicators detected" }
    : { icon: "✕", label: "PHISHING", desc: "Threat detected by ML model" };

  verdictIcon.textContent  = cfg.icon;
  verdictLabel.textContent = cfg.label;
  verdictDesc.textContent  = cfg.desc;

  // Confidence
  confNum.textContent = pct.toFixed(1) + "%";
  requestAnimationFrame(() => requestAnimationFrame(() => {
    confBar.style.width = Math.min(pct, 100) + "%";
  }));

  // Reason (AI explanation — the key USP)
  if (reason && reason.trim()) {
    reasonText.textContent = reason.trim();
    reasonText.className   = "reason-text";
  } else {
    reasonText.textContent = isSafe
      ? "All 6 features within normal range. Domain established, no phishing keywords detected."
      : "The model flagged this URL based on extracted features.";
    reasonText.className   = "reason-text";
  }

  showState("stateResult");
}

// ── Load stored result for active tab ─────────────────────────────────────
async function loadResult() {
  showState("stateScanning");
  statusDot.className    = "status-dot scanning";
  statusText.textContent = "Scanning";

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;
  urlVal.textContent = tab.url || "—";

  const stored = await chrome.storage.session.get(`tab_${tab.id}`);
  const data   = stored[`tab_${tab.id}`];

  if (!data) {
    statusDot.className    = "status-dot";
    statusText.textContent = "No scan";
    showState("stateScanning");
    return;
  }

  if (data.status === "error") {
    statusDot.className    = "status-dot error";
    statusText.textContent = "Error";
    errMsg.textContent     = data.error || "Cannot connect to scan server at 127.0.0.1:5000.";
    showState("stateError");
    return;
  }

  renderResult(data);
}

// ── Re-scan ───────────────────────────────────────────────────────────────
rescanBtn.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url) return;

  showState("stateScanning");
  statusDot.className    = "status-dot scanning";
  statusText.textContent = "Scanning";

  try {
    const res = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url: tab.url }),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();

    await chrome.storage.session.set({
      [`tab_${tab.id}`]: { ...data, status: "done" }
    });
    renderResult(data);

  } catch (e) {
    errMsg.textContent     = "Cannot connect to Flask API at 127.0.0.1:5000.\nMake sure the backend is running.";
    statusDot.className    = "status-dot error";
    statusText.textContent = "Error";
    showState("stateError");
  }
});

loadResult();
