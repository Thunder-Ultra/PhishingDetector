// Keep a list of URLs the user chose to "Proceed Anyway"
let whitelistedUrls = new Set();

browser.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Only scan when the URL changes and it is a real website (http/https)
    if (changeInfo.url && tab.url.startsWith('http')) {
        let currentUrl = tab.url;

        // If user already whitelisted this site, let them browse seamlessly
        if (whitelistedUrls.has(currentUrl)) return;

        try {
            // Silently scan the URL in the background via Flask API
            let response = await fetch('http://127.0.0.1:5000/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl })
            });
            
            let data = await response.json();

            // If AI says it's phishing, forcefully redirect to the full-screen block page
            if (data.result === "phishing") {
                let blockUrl = browser.runtime.getURL("block.html") + 
                    "?url=" + encodeURIComponent(currentUrl) + 
                    "&confidence=" + data.confidence + 
                    "&reason=" + encodeURIComponent(data.reason);
                
                browser.tabs.update(tabId, { url: blockUrl });
            }

        } catch (error) {
            console.log("PhishGuard Backend offline or connection refused.");
        }
    }
});

// Listen for the "Proceed Anyway" button click from the block page
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "whitelist" && message.url) {
        whitelistedUrls.add(message.url);
        browser.tabs.update(sender.tab.id, { url: message.url }); // Send them back to the site
    }
});