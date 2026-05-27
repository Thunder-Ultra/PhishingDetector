/**
 * content.js — PhishGuard Content Script v5
 * Shows a safe badge with the AI reason string on legitimate sites.
 */

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "SITE_SAFE") showSafeBadge(msg.confidence, msg.reason);
});

function showSafeBadge(confidence, reason) {
  if (document.getElementById("pg-badge")) return;

  const badge = document.createElement("div");
  badge.id = "pg-badge";
  badge.innerHTML = `
    <style>
      #pg-badge {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 2147483646;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        background: rgba(8,10,15,0.96);
        border: 1px solid rgba(34,197,94,0.35);
        border-radius: 14px;
        padding: 11px 14px 11px 12px;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.45);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        opacity: 0;
        transform: translateY(12px) scale(0.96);
        transition: opacity 0.3s ease, transform 0.3s ease;
        max-width: 280px;
      }
      #pg-badge.visible { opacity: 1; transform: translateY(0) scale(1); }
      #pg-badge-icon {
        width: 34px; height: 34px; flex-shrink: 0;
        background: rgba(34,197,94,0.12);
        border: 1px solid rgba(34,197,94,0.28);
        border-radius: 9px;
        display: flex; align-items: center; justify-content: center;
        font-size: 17px;
        margin-top: 1px;
      }
      #pg-badge-content { display: flex; flex-direction: column; gap: 3px; flex: 1; }
      #pg-badge-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
      #pg-badge-pct { font-size: 13px; font-weight: 700; color: #22c55e; line-height: 1; }
      #pg-badge-sub { font-size: 10px; color: #6b7280; letter-spacing: 0.4px; }
      #pg-badge-reason {
        font-size: 10.5px;
        color: #9ca3af;
        line-height: 1.45;
        margin-top: 1px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      #pg-badge-close {
        background: none; border: none; color: #4b5563; font-size: 13px;
        cursor: pointer; padding: 0; line-height: 1; flex-shrink: 0;
        transition: color 0.2s; margin-top: 1px;
      }
      #pg-badge-close:hover { color: #9ca3af; }
    </style>
    <div id="pg-badge-icon">🛡️</div>
    <div id="pg-badge-content">
      <div id="pg-badge-top">
        <span id="pg-badge-pct">${confidence.toFixed(1)}% Safe</span>
        <span id="pg-badge-sub">PhishGuard</span>
        <button id="pg-badge-close">✕</button>
      </div>
      ${reason ? `<div id="pg-badge-reason">${reason}</div>` : ""}
    </div>
  `;

  document.body.appendChild(badge);
  requestAnimationFrame(() => requestAnimationFrame(() => badge.classList.add("visible")));

  const timer = setTimeout(() => dismiss(), 6000);
  badge.querySelector("#pg-badge-close").onclick = () => { clearTimeout(timer); dismiss(); };

  function dismiss() {
    badge.classList.remove("visible");
    setTimeout(() => badge.remove(), 350);
  }
}
