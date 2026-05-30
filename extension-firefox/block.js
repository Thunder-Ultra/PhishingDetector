document.addEventListener('DOMContentLoaded', () => {
    // Get the blocked data from the URL parameters passed by background.js
    const urlParams = new URLSearchParams(window.location.search);
    const blockedUrl = urlParams.get('url');
    const ai_confidence = parseFloat(urlParams.get('confidence'));
    const ai_reason = urlParams.get('reason');

    // DOM Elements
    const statusEl = document.getElementById("status");
    const reasonEl = document.getElementById("reason");
    const urlEl = document.getElementById("scanned-url");
    const confBar = document.getElementById("confidence-bar");
    const confValue = document.getElementById("confidence-value");
    const badgeEl = document.getElementById("badge-status");
    const mainCard = document.getElementById("main-card");
    const iconContainer = document.getElementById("icon-container");
    const brandDot = document.querySelector(".brand .dot");

    // Populate the UI
    urlEl.innerText = blockedUrl;
    reasonEl.innerText = ai_reason;
    confBar.style.width = ai_confidence + "%";
    confValue.innerText = ai_confidence + "%";

    // Apply Tier 2 or Tier 3 styling based on confidence
    if (ai_confidence > 75.0) {
        statusEl.innerText = "🚨 DANGER: Phishing Detected (" + ai_confidence + "%)";
        statusEl.style.color = "#dc2626"; // Red
        badgeEl.style.borderColor = "#dc2626";
        badgeEl.style.color = "#dc2626";
        confBar.style.backgroundColor = "#dc2626";
        iconContainer.style.color = "#dc2626";
        brandDot.style.backgroundColor = "#dc2626";
    } else {
        statusEl.innerText = "⚠️ SUSPICIOUS: Proceed with caution";
        statusEl.style.color = "#d97706"; // Orange
        badgeEl.innerText = "WARNING";
        badgeEl.style.borderColor = "#d97706";
        badgeEl.style.color = "#d97706";
        confBar.style.backgroundColor = "#d97706";
        iconContainer.style.color = "#d97706";
        brandDot.style.backgroundColor = "#d97706";
    }

    // Button Actions
    document.getElementById("btn-back").addEventListener('click', () => {
        // Close the dangerous tab or go back
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.close();
        }
    });

    document.getElementById("btn-proceed").addEventListener('click', () => {
        // Tell background.js to whitelist this URL and redirect back to it
        chrome.runtime.sendMessage({ action: "whitelist", url: blockedUrl });
    });

    document.getElementById("btn-report").addEventListener('click', () => {
        alert("Reported to retraining queue. Thank you!");
        chrome.runtime.sendMessage({ action: "report", url: blockedUrl });
    });
});