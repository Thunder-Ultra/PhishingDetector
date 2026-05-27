/**
 * background.js — PhishGuard Service Worker v5
 *
 * API: POST http://127.0.0.1:5000/predict
 * Response: { url, result: "safe"|"phishing", confidence, reason }
 */

const API_URL        = "http://127.0.0.1:5000/predict";
const CACHE_TTL      = 5 * 60 * 1000;  // 5 min
const API_TIMEOUT_MS = 10000;           // 10s — WHOIS can be slow

const scanCache = new Map();
const inFlight  = new Set();
const allowOnce = new Set();

function baseUrl(url) {
  return url.split("?")[0].split("#")[0];
}

// ── Intercept every navigation ────────────────────────────────────────────
chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  if (details.frameId !== 0) return;
  if (!details.url.startsWith("http")) return;
  if (details.url.startsWith("chrome-extension://")) return;
  if (details.url.includes(chrome.runtime.id)) return;

  const url   = details.url;
  const base  = baseUrl(url);
  const tabId = details.tabId;

  if (allowOnce.has(base)) { allowOnce.delete(base); return; }
  if (inFlight.has(tabId)) return;
  inFlight.add(tabId);

  try {
    const cached = scanCache.get(base);
    const now    = Date.now();
    const data   = (cached && now - cached.ts < CACHE_TTL)
      ? cached
      : await fetchWithTimeout(url);

    if (!cached || now - cached.ts >= CACHE_TTL) {
      scanCache.set(base, { ...data, ts: now });
    }

    if (data.result === "phishing") {
      const payload = {
        url,
        baseUrl: base,
        result:     data.result,
        confidence: Number(data.confidence),
        reason:     data.reason || "",
        ts: now,
      };

      await chrome.storage.local.set({ [`blocked_${tabId}`]: payload });

      const blockedPage = chrome.runtime.getURL("blocked.html");
      await chrome.tabs.update(tabId, { url: `${blockedPage}?tab=${tabId}` });

    } else {
      // Safe — store for popup
      chrome.storage.session.set({
        [`tab_${tabId}`]: { url, ...data, status: "done" }
      }).catch(() => {});
    }

  } catch (err) {
    console.warn("[PhishGuard] scan error:", err.message);
    // Fail open — if backend is down, let user through
  } finally {
    setTimeout(() => inFlight.delete(tabId), 3000);
  }

}, { url: [{ schemes: ["http", "https"] }] });

// ── Show safe badge ───────────────────────────────────────────────────────
chrome.webNavigation.onCommitted.addListener(async (details) => {
  if (details.frameId !== 0) return;
  if (!details.url.startsWith("http")) return;
  if (details.url.includes(chrome.runtime.id)) return;

  const tabId  = details.tabId;
  const stored = await chrome.storage.session.get(`tab_${tabId}`).catch(() => ({}));
  const data   = stored[`tab_${tabId}`];

  if (data?.status === "done" && data.result === "safe") {
    setTimeout(() => {
      chrome.tabs.sendMessage(tabId, {
        type:       "SITE_SAFE",
        confidence: data.confidence,
        reason:     data.reason || "",
        url:        details.url,
      }).catch(() => {});
    }, 900);
  }
});

// ── API call with timeout ─────────────────────────────────────────────────
async function fetchWithTimeout(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  try {
    const res = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url }),
      signal:  controller.signal,
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

// ── Messages from blocked.html / blocked.js ───────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  if (msg.type === "OPEN_NEWTAB") {
    chrome.tabs.create({ url: "chrome://newtab/" });
    sendResponse({ ok: true });
    return true;
  }

  if (msg.type === "ALLOW_ONCE" && msg.url) {
    const base = baseUrl(msg.url);
    allowOnce.add(base);
    allowOnce.add(msg.url);
    setTimeout(() => {
      allowOnce.delete(base);
      allowOnce.delete(msg.url);
    }, 10000);
    sendResponse({ ok: true });
    return true;
  }

  if (msg.type === "CLEAN_STORAGE" && msg.tabId) {
    chrome.storage.local.remove(`blocked_${msg.tabId}`);
    sendResponse({ ok: true });
    return true;
  }
});

// ── Cleanup on tab close ──────────────────────────────────────────────────
chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.local.remove(`blocked_${tabId}`);
  chrome.storage.session.remove(`tab_${tabId}`).catch(() => {});
  inFlight.delete(tabId);
});
