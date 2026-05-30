document.addEventListener('DOMContentLoaded', async () => {
    const statusEl = document.getElementById("status");
    const reasonEl = document.getElementById("reason");
    const urlEl = document.getElementById("scanned-url");
    const confBar = document.getElementById("confidence-bar");
    const confValue = document.getElementById("confidence-value");
    const badgeEl = document.getElementById("badge-status");
    const iconContainer = document.getElementById("icon-container");
    const brandDot = document.querySelector(".brand .dot");
    
    const reportBtn = document.getElementById("btn-report");
    const backBtn = document.getElementById("btn-back");
    const recheckBtn = document.getElementById("btn-recheck");

    let currentUrl = "";

    // Button Listeners
    reportBtn.addEventListener('click', () => { 
        alert("Reported to retraining queue as a false prediction. Thank you!"); 
        chrome.runtime.sendMessage({ action: "report", url: currentUrl });
    });
    
    backBtn.addEventListener('click', () => { window.close(); });
    
    recheckBtn.addEventListener('click', () => {
        // Reset UI to scanning state and force a recheck
        statusEl.innerText = "Scanning Website...";
        statusEl.style.color = "#c9d1d9";
        reasonEl.innerText = "Analyzing URL features with XGBoost...";
        confBar.style.width = "0%";
        confValue.innerText = "--%";
        badgeEl.innerText = "SCANNING";
        badgeEl.style.color = "#8b949e";
        badgeEl.style.borderColor = "#30363d";
        iconContainer.style.color = "#8b949e";
        brandDot.style.backgroundColor = "#8b949e";
        
        fetchAndScan(currentUrl, true);
    });

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        currentUrl = tab.url;
        
        // Prevent scanning the extension's own block page
        if (currentUrl.startsWith("chrome-extension://")) {
            urlEl.innerText = "Internal Extension Page";
            statusEl.innerText = "System Page";
            return;
        }

        urlEl.innerText = currentUrl;

        // CHECK CACHE FIRST: Fulfills Requirement #2
        let cache = await chrome.storage.local.get([currentUrl]);
        if (cache[currentUrl]) {
            updateUI(cache[currentUrl]);
        } else {
            fetchAndScan(currentUrl, false);
        }

    } catch (error) {
        showError();
    }

    async function fetchAndScan(url, forceRecheck) {
        try {
            let response = await fetch('http://127.0.0.1:5000/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });
            
            let data = await response.json();
            
            // Cache the new result
            await chrome.storage.local.set({ [url]: data });
            
            updateUI(data);
        } catch (error) {
            showError();
        }
    }

    // Inside popup.js, replace the updateUI function with this:

    function updateUI(data) {
                if (data.error) {
            statusEl.innerText = "Backend Error";
            reasonEl.innerText = data.error;
            return;
        }
        
        let ai_verdict = data.result;
        
        let ai_confidence = data.confidence; 

        confBar.style.width = ai_confidence + "%";
        confValue.innerText = ai_confidence + "%";
        reasonEl.innerText = data.reason; // This will now display the text from Python!

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
        } else if (ai_verdict === "suspicious") {
            // FIX: Added the missing Orange Warning Tier
            statusEl.innerText = "⚠️ Suspicious Website";
            statusEl.style.color = "#d97706"; 
            badgeEl.innerText = "WARNING";
            badgeEl.style.borderColor = "#d97706";
            badgeEl.style.color = "#d97706";
            confBar.style.backgroundColor = "#d97706";
            iconContainer.style.color = "#d97706";
            brandDot.style.backgroundColor = "#d97706";
            backBtn.innerText = "Proceed with Caution";
            backBtn.style.background = "linear-gradient(90deg, #d97706, #b45309)";
        } else {
            statusEl.innerText = "🚨 Phishing Detected";
            statusEl.style.color = "#dc2626"; 
            badgeEl.innerText = "DANGER";
            badgeEl.style.borderColor = "#dc2626";
            badgeEl.style.color = "#dc2626";
            confBar.style.backgroundColor = "#dc2626";
            iconContainer.style.color = "#dc2626";
            brandDot.style.backgroundColor = "#dc2626";
            backBtn.innerText = "← Go Back to Safety";
            backBtn.style.background = "linear-gradient(90deg, #3b82f6, #2563eb)";
        }
    }

    function showError() {
        statusEl.innerText = "Connection Error";
        reasonEl.innerText = "Ensure Flask backend is running at http://127.0.0.1:5000";
    }
});