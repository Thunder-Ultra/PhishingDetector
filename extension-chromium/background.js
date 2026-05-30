// Keep a list of URLs the user chose to "Proceed Anyway" so we don't block them in an infinite loop
let whitelistedUrls = new Set();

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Only scan when the URL changes and it is a real website (http/https)
    if (changeInfo.status === 'loading' && tab.url && tab.url.startsWith('http')) {
        let currentUrl = tab.url;

        // Check session storage instead of the volatile Set
        let session = await chrome.storage.session.get({ whitelistedUrls: [] });
        if (session.whitelistedUrls.includes(currentUrl)) return;

        try {
            // Silently scan the URL in the background
            let response = await fetch('http://127.0.0.1:5000/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl })
            });
            
            let data = await response.json();

            // CACHE THE RESULT: Prevents the popup from re-checking when opened
            await chrome.storage.local.set({ [currentUrl]: data });

            // If the AI says it's phishing, forcefully redirect to the full-screen block page
                        if (data.result === "phishing" || data.result === "suspicious") {
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

// Listen for messages from block.js or popup.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "whitelist" && message.url) {
        chrome.storage.session.get({ whitelistedUrls: [] }, (res) => {
            let list = res.whitelistedUrls;
            if (!list.includes(message.url)) list.push(message.url);
            chrome.storage.session.set({ whitelistedUrls: list });
            
            chrome.tabs.update(sender.tab.id, { url: message.url }); 
        });
    }
    // ... (report logic remains the same)
});