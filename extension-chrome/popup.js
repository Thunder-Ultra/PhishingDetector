document.addEventListener('DOMContentLoaded', async () => {
    const statusEl = document.getElementById("status");
    const reasonEl = document.getElementById("reason");
    const urlEl = document.getElementById("scanned-url");
    const confBar = document.getElementById("confidence-bar");
    const confValue = document.getElementById("confidence-value");
    const badgeEl = document.getElementById("badge-status");
    const mainCard = document.getElementById("main-card");
    const iconContainer = document.getElementById("icon-container");
    const brandDot = document.querySelector(".brand .dot");
    
    const reportBtn = document.getElementById("btn-report");
    const backBtn = document.getElementById("btn-back");

    reportBtn.addEventListener('click', () => { alert("Reported to retraining queue."); });
    backBtn.addEventListener('click', () => { window.close(); });

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        let currentUrl = tab.url;
        
        // Prevent scanning the extension's own block page
        if (currentUrl.startsWith("chrome-extension://")) {
            urlEl.innerText = "Internal Extension Page";
            statusEl.innerText = "System Page";
            return;
        }

        urlEl.innerText = currentUrl;

        let response = await fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: currentUrl })
        });
        
        let data = await response.json();
        let ai_verdict = data.result; 
        let ai_confidence = data.confidence; 

        confBar.style.width = ai_confidence + "%";
        confValue.innerText = ai_confidence + "%";
        reasonEl.innerText = data.reason;

        if (ai_verdict === "safe") {
            statusEl.innerText = "✅ Safe Website";
            statusEl.style.color = "#16a34a"; 
            badgeEl.innerText = "SAFE";
            badgeEl.style.borderColor = "#16a34a";
            badgeEl.style.color = "#16a34a";
            confBar.style.backgroundColor = "#16a34a";
            iconContainer.style.color = "#16a34a";
            brandDot.style.backgroundColor = "#16a34a";
            backBtn.innerText = "Continue Browsing";
            backBtn.style.background = "linear-gradient(90deg, #16a34a, #15803d)";
        }
    } catch (error) {
        statusEl.innerText = "Connection Error";
        reasonEl.innerText = "Ensure Flask backend is running at http://127.0.0.1:5000";
    }
});