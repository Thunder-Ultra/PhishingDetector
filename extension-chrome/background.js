// Keep a list of URLs the user chose to "Proceed Anyway" so we don't block them in an infinite loop
let whitelistedUrls = new Set();

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Only scan when the URL changes and it is a real website (http/https)
    if (changeInfo.url && tab.url.startsWith('http')) {
        let currentUrl = tab.url;

        // If user already clicked "Proceed Anyway" for this site, let them browse
        if (whitelistedUrls.has(currentUrl)) return;

        try {
            // Silently scan the URL in the background
            let response = await fetch('http://127.0.0.1:5000/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl })
            });
            
            let data = await response.json();

            // If the AI says it's phishing, forcefully redirect to the full-screen block page
            if (data.result === "phishing") {
                let blockUrl = chrome.runtime.getURL("block.html") + 
                    "?url=" + encodeURIComponent(currentUrl) + 
                    "&confidence=" + data.confidence + 
                    "&reason=" + encodeURIComponent(data.reason);
                
                chrome.tabs.update(tabId, { url: blockUrl });
            }
            // If safe, do nothing! The user continues browsing seamlessly.

        } catch (error) {
            console.log("PhishGuard Backend offline or scanning error.");
        }
    }
});

// Listen for the "Proceed Anyway" button click from block.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "whitelist" && message.url) {
        whitelistedUrls.add(message.url);
        chrome.tabs.update(sender.tab.id, { url: message.url }); // Send them back to the site
    }
});