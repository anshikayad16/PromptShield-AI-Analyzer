// Background service worker for ShieldAI
chrome.runtime.onInstalled.addListener(() => {
    console.log("ShieldAI Extension Installed");
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "ANALYZE_PROMPT") {
        const payload = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: request.prompt })
        };

        // Try 127.0.0.1 first, fallback to localhost
        fetch('http://127.0.0.1:5000/api/analyze', payload)
            .catch(err => {
                console.warn("127.0.0.1 fetch failed, trying localhost...", err);
                return fetch('http://localhost:5000/api/analyze', payload);
            })
            .then(res => {
                if (!res.ok) {
                    throw new Error("HTTP Status: " + res.status);
                }
                return res.json();
            })
            .then(data => sendResponse(data))
            .catch(err => sendResponse({ error: err.toString() }));
            
        return true; // Keep message channel open for async response
    }
});
