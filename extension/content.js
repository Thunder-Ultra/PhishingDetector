/**
 * content.js — PhishGuard Content Script
 * Shows a sleek safe badge on legitimate sites.
 */

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "SITE_SAFE") showSafeBadge(msg.confidence);
});

function showSafeBadge(confidence) {
  if (document.getElementById("pg-badge")) return;

  const badge = document.createElement("div");
  badge.id = "pg-badge";
  badge.innerHTML = `
    <style>
      #pg-badge {
        position: fixed;
        bottom: 28px;
        right: 28px;
        z-index: 2147483646;
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(10,12,16,0.95);
        border: 1px solid rgba(34,197,94,0.4);
        border-radius: 14px;
        padding: 10px 16px 10px 12px;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(34,197,94,0.15);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        opacity: 0;
        transform: translateY(10px) scale(0.95);
        transition: opacity 0.35s ease, transform 0.35s ease;
        cursor: default;
      }
      #pg-badge.visible {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
      #pg-badge-icon {
        width: 32px; height: 32px;
        background: rgba(34,197,94,0.15);
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px;
      }
      #pg-badge-text { display: flex; flex-direction: column; gap: 1px; }
      #pg-badge-pct  { font-size: 13px; font-weight: 700; color: #22c55e; line-height: 1; }
      #pg-badge-sub  { font-size: 10px; color: #6b7280; letter-spacing: 0.5px; }
      #pg-badge-close {
        background: none; border: none; color: #4b5563; font-size: 14px;
        cursor: pointer; padding: 2px; margin-left: 4px; line-height: 1;
        transition: color 0.2s;
      }
      #pg-badge-close:hover { color: #9ca3af; }
    </style>
    <div id="pg-badge-icon">🛡️</div>
    <div id="pg-badge-text">
      <span id="pg-badge-pct">${confidence.toFixed(1)}% Safe</span>
      <span id="pg-badge-sub">PhishGuard</span>
    </div>
    <button id="pg-badge-close">✕</button>
  `;

  document.body.appendChild(badge);
  requestAnimationFrame(() => requestAnimationFrame(() => badge.classList.add("visible")));

  const timer = setTimeout(() => dismiss(), 5000);
  badge.querySelector("#pg-badge-close").onclick = () => { clearTimeout(timer); dismiss(); };

  function dismiss() {
    badge.classList.remove("visible");
    setTimeout(() => badge.remove(), 400);
  }
}
