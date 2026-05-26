/**
 * popup.js — PhishGuard Popup Logic
 * Reads scan result from session storage. Re-scan triggers fresh API call.
 */

const API_URL = "http://localhost:5000/predict";

// DOM refs
const urlVal       = document.getElementById("urlVal");
const statusDot    = document.getElementById("statusDot");
const statusText   = document.getElementById("statusText");
const stateScanning= document.getElementById("stateScanning");
const stateResult  = document.getElementById("stateResult");
const stateError   = document.getElementById("stateError");
const verdictRing  = document.getElementById("verdictRing");
const verdictIcon  = document.getElementById("verdictIcon");
const verdictLabel = document.getElementById("verdictLabel");
const verdictDesc  = document.getElementById("verdictDesc");
const confNum      = document.getElementById("confNum");
const confBar      = document.getElementById("confBar");
const featuresGrid = document.getElementById("featuresGrid");
const errMsg       = document.getElementById("errMsg");
const rescanBtn    = document.getElementById("rescanBtn");

const ROOT = document.documentElement;

function showState(id) {
  [stateScanning, stateResult, stateError].forEach(el => el.classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
}

function applyTheme(result) {
  const themes = {
    safe:      { c: "#2dd98f", s: "rgba(45,217,143,0.10)",  b: "rgba(45,217,143,0.25)" },
    phishing:  { c: "#f25c5c", s: "rgba(242,92,92,0.10)",   b: "rgba(242,92,92,0.28)"  },
    suspicious:{ c: "#f5a623", s: "rgba(245,166,35,0.10)",  b: "rgba(245,166,35,0.28)" },
    error:     { c: "#5a6580", s: "rgba(90,101,128,0.10)",  b: "rgba(90,101,128,0.25)" },
  };
  const t = themes[result] || themes.error;
  ROOT.style.setProperty("--rc",  t.c);
  ROOT.style.setProperty("--rcs", t.s);
  ROOT.style.setProperty("--rcb", t.b);
}

function renderResult(data) {
  const { result, confidence, features } = data;
  applyTheme(result);

  // Status pill
  statusDot.className  = `status-dot ${result === "safe" ? "safe" : "danger"}`;
  statusText.textContent = result.toUpperCase();

  // Verdict content
  const configs = {
    safe:       { icon: "✓", label: "SAFE",       desc: "No phishing indicators detected" },
    phishing:   { icon: "✕", label: "PHISHING",   desc: "Threat blocked — high-risk URL" },
    suspicious: { icon: "⚑", label: "SUSPICIOUS", desc: "Multiple risk factors detected" },
  };
  const cfg = configs[result] || { icon: "?", label: "UNKNOWN", desc: "Could not classify" };

  verdictIcon.textContent  = cfg.icon;
  verdictLabel.textContent = cfg.label;
  verdictDesc.textContent  = cfg.desc;

  // Confidence
  const pct = parseFloat(confidence) || 0;
  confNum.textContent = pct.toFixed(1) + "%";
  requestAnimationFrame(() => requestAnimationFrame(() => {
    confBar.style.width = pct + "%";
  }));

  // Feature chips
  featuresGrid.innerHTML = "";
  (features || []).forEach(f => {
    const chip = document.createElement("div");
    chip.className   = "feat-chip" + (f.flagged ? " flagged" : "");
    chip.textContent = f.name;
    featuresGrid.appendChild(chip);
  });

  showState("stateResult");
}

// ── Load result for active tab ────────────────────────────────────────────
async function loadResult() {
  showState("stateScanning");
  statusDot.className  = "status-dot scanning";
  statusText.textContent = "Scanning";

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  urlVal.textContent = tab.url || "—";

  const stored = await chrome.storage.session.get(`tab_${tab.id}`);
  const data   = stored[`tab_${tab.id}`];

  if (!data) {
    statusDot.className  = "status-dot";
    statusText.textContent = "No scan";
    showState("stateScanning");
    return;
  }

  if (data.status === "error") {
    statusDot.className   = "status-dot error";
    statusText.textContent = "Error";
    errMsg.textContent    = data.error || "Cannot connect to scan server.";
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
  statusDot.className  = "status-dot scanning";
  statusText.textContent = "Scanning";

  try {
    const res  = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url: tab.url }),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    await chrome.storage.session.set({
      [`tab_${tab.id}`]: { ...data, url: tab.url, status: "done" }
    });
    renderResult(data);
  } catch (e) {
    errMsg.textContent = "Cannot connect to Flask API on localhost:5000.";
    showState("stateError");
    statusDot.className  = "status-dot error";
    statusText.textContent = "Error";
  }
});

loadResult();
