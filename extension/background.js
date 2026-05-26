/**
 * background.js — PhishGuard Service Worker
 *
 * Checks (all on URL before '?'):
 *   1. Dots in domain
 *   2. Forward slashes in path
 *   3. URL length
 *   4. Domain age (WHOIS — done server-side)
 *   5. HTML keyword count (login, password, verify, back,
 *                          secure, account, update, suspended)
 */

const API_URL        = "http://localhost:5000/predict";
const CACHE_TTL      = 5 * 60 * 1000;  // 5 min cache
// HTML fetch + WHOIS can take a few seconds — give backend 8 seconds
const API_TIMEOUT_MS = 8000;

const scanCache = new Map();
const inFlight  = new Set();
// allowOnce stores BASE URLs (before '?') so re-block doesn't fire
const allowOnce = new Set();

// ── Strip query string — backend only uses base URL ──────────────────────
function baseUrl(url) {
  return url.split("?")[0].split("#")[0];
}

// ── Intercept every navigation before the page loads ─────────────────────
chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  if (details.frameId !== 0) return;
  if (!details.url.startsWith("http")) return;
  if (details.url.startsWith("chrome-extension://")) return;
  if (details.url.includes(chrome.runtime.id)) return;

  const url     = details.url;
  const base    = baseUrl(url);
  const tabId   = details.tabId;

  // "Proceed Anyway" bypass — match on base URL (no query string)
  if (allowOnce.has(base)) {
    allowOnce.delete(base);
    return;
  }

  if (inFlight.has(tabId)) return;
  inFlight.add(tabId);

  try {
    // Cache key = base URL (no query string, same page = same scan)
    const cached = scanCache.get(base);
    const now    = Date.now();
    const data   = (cached && now - cached.ts < CACHE_TTL)
      ? cached
      : await fetchWithTimeout(url);   // send full URL; backend strips ?

    if (!cached || now - cached.ts >= CACHE_TTL) {
      scanCache.set(base, { ...data, ts: now });
    }

    if (data.result === "phishing" || data.result === "suspicious") {
      // Only keep flagged features for the blocked page display
      const flagged = (data.features || [])
        .filter(f => f.flagged)
        .map(f => f.name);

      const payload = {
        url,          // full original URL (shown to user)
        baseUrl: base,
        result:     data.result,
        confidence: Number(data.confidence),
        flagged,
        ts: now,
      };

      // Store in local storage — blocked.html reads this by tabId
      await chrome.storage.local.set({ [`blocked_${tabId}`]: payload });

      // Redirect — only tabId in the URL, no encoding nightmares
      const blockedPage = chrome.runtime.getURL("blocked.html");
      await chrome.tabs.update(tabId, { url: `${blockedPage}?tab=${tabId}` });

    } else {
      // Safe — store for popup badge
      chrome.storage.session.set({
        [`tab_${tabId}`]: { url, ...data, status: "done" }
      }).catch(() => {});
    }

  } catch (err) {
    console.warn("[PhishGuard] scan error:", err.message);
    // Fail open — if backend is down, let the user through
  } finally {
    setTimeout(() => inFlight.delete(tabId), 3000);
  }

}, { url: [{ schemes: ["http", "https"] }] });

// ── Show safe badge on safe pages ─────────────────────────────────────────
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
        features:   data.features || [],
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

// ── Messages from blocked.html ────────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  // "Go Back to Safety" — open new tab (can't navigate chrome:// from page JS)
  if (msg.type === "OPEN_NEWTAB") {
    chrome.tabs.create({ url: "chrome://newtab/" });
    sendResponse({ ok: true });
    return true;
  }

  // "Proceed Anyway" — whitelist the base URL so intercept skips it once
  if (msg.type === "ALLOW_ONCE" && msg.url) {
    const base = baseUrl(msg.url);
    allowOnce.add(base);
    // Also add the full URL in case navigation uses exact URL
    allowOnce.add(msg.url);
    setTimeout(() => {
      allowOnce.delete(base);
      allowOnce.delete(msg.url);
    }, 10000); // 10s window to actually navigate
    sendResponse({ ok: true });
    return true;
  }

  // Clean up storage after blocked.html has rendered
  if (msg.type === "CLEAN_STORAGE" && msg.tabId) {
    chrome.storage.local.remove(`blocked_${msg.tabId}`);
    sendResponse({ ok: true });
    return true;
  }
});

// ── Clean up on tab close ─────────────────────────────────────────────────
chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.local.remove(`blocked_${tabId}`);
  chrome.storage.session.remove(`tab_${tabId}`).catch(() => {});
  inFlight.delete(tabId);
});