/**
 * blocked.js — PhishGuard Blocked Page Logic v5
 *
 * Reads from chrome.storage.local:
 *   { url, result, confidence, reason }
 *
 * The `reason` string is the explainability hero — shown prominently.
 */

(async function init() {
  const params = new URLSearchParams(location.search);
  const tabId  = params.get("tab");

  // Load from storage (with one retry)
  let d = null;
  for (let attempt = 0; attempt < 2; attempt++) {
    if (attempt > 0) await new Promise(r => setTimeout(r, 300));
    if (!tabId) break;
    try {
      const res = await chrome.storage.local.get("blocked_" + tabId);
      d = res["blocked_" + tabId] || null;
      if (d) break;
    } catch(e) { console.error("[PhishGuard] storage error:", e); }
  }

  const url        = d?.url        || location.href;
  const result     = d?.result     || "phishing";
  const confidence = Number(d?.confidence ?? 85);
  const reason     = d?.reason     || "";

  // Fill UI
  document.getElementById("confBig").textContent = confidence.toFixed(1) + "%";
  document.getElementById("confRisk").textContent =
    confidence >= 85 ? "CRITICAL" :
    confidence >= 70 ? "HIGH"     :
    confidence >= 55 ? "MEDIUM"   : "LOW";

  // Animate bar
  requestAnimationFrame(() => requestAnimationFrame(() => {
    document.getElementById("barFill").style.width = Math.min(confidence, 100) + "%";
  }));

  document.getElementById("urlBox").textContent = url;

  // Reason — the explainability hero
  document.getElementById("reasonText").textContent = reason.trim()
    || "The model detected suspicious patterns in this URL based on dots, slashes, domain age, and keyword analysis.";

  // Buttons
  document.getElementById("btnBack").addEventListener("click", () => {
    if (history.length > 1) {
      history.back();
    } else {
      chrome.runtime.sendMessage({ type: "OPEN_NEWTAB" }).catch(() => {});
    }
  });

  document.getElementById("btnProceed").addEventListener("click", () => {
    const ok = confirm(
      "⚠️  PhishGuard Warning\n\n" +
      "The AI reason: " + (reason || "Phishing indicators detected") + "\n\n" +
      "Confidence: " + confidence.toFixed(1) + "%\n\n" +
      "Proceeding may expose your data. Are you absolutely sure?"
    );
    if (ok) {
      chrome.runtime.sendMessage({ type: "ALLOW_ONCE", url })
        .catch(() => {})
        .finally(() => { window.location.href = url; });
    }
  });

  // Clean storage
  if (tabId) {
    chrome.runtime.sendMessage({ type: "CLEAN_STORAGE", tabId: Number(tabId) }).catch(() => {});
  }

})();
