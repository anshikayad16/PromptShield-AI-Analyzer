// Create toast notification element
const toast = document.createElement('div');
toast.className = 'shield-ai-toast';
document.body.appendChild(toast);

function showToast(message, type) {
    toast.textContent = message;
    toast.className = `shield-ai-toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

// Flag to prevent recursion when we manually re-fire the Enter key
let isReplayingEvent = false;

// We use the "capture" phase (true) so we intercept the Enter key BEFORE 
// the website's own React/Vue/VanillaJS scripts can see it and send the prompt!
document.addEventListener('keydown', async function(e) {
    // If we already verified it, let the event pass through to the LLM website
    if (isReplayingEvent) return;

    if (e.key === 'Enter' && !e.shiftKey) {
        const el = e.target;
        
        // Are they typing in a text area or message box?
        if (el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && el.type === 'text') || el.isContentEditable) {
            
            let promptText = "";
            if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                promptText = el.value;
            } else {
                promptText = el.innerText;
            }

            if (!promptText || !promptText.trim()) return;

            // PAUSE THE SUBMISSION
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            // Handle "Extension context invalidated" error (happens after extension reload)
            if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.sendMessage) {
                showToast("⚠️ Extension reloaded. Please refresh the page.", "blocked");
                console.error("ShieldAI Error: Extension context invalidated. Please refresh the page.");
                return;
            }

            showToast("🛡️ ShieldAI: Analyzing prompt...", "analyzing");

            try {
                const data = await new Promise((resolve, reject) => {
                    chrome.runtime.sendMessage({ type: "ANALYZE_PROMPT", prompt: promptText.trim() }, (response) => {
                        if (chrome.runtime.lastError) {
                            return reject(new Error(chrome.runtime.lastError.message));
                        }
                        if (response && response.error) {
                            return reject(new Error(response.error));
                        }
                        resolve(response);
                    });
                });
                
                if (data.status === 'Safe') {
                    showToast("✓ Safe! Passing to LLM...", "safe");
                    
                    // RE-FIRE THE EVENT to let the LLM website process it
                    isReplayingEvent = true;
                    
                    const enterEvent = new KeyboardEvent('keydown', {
                        bubbles: true,
                        cancelable: true,
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13
                    });
                    el.dispatchEvent(enterEvent);
                    
                    // Some sites might use keyup, so let's fire that too if needed
                    const keyupEvent = new KeyboardEvent('keyup', {
                        bubbles: true, cancelable: true, key: 'Enter', code: 'Enter', keyCode: 13
                    });
                    el.dispatchEvent(keyupEvent);
                    
                    isReplayingEvent = false;
                } else {
                    // BLOCKED! Do not replay the event.
                    showToast(`⚠️ Blocked by ${data.layer}: ${data.reason}`, "blocked");
                    
                    // Optional visual cue on the text box
                    const originalBg = el.style.backgroundColor;
                    el.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                    setTimeout(() => {
                        el.style.backgroundColor = originalBg;
                    }, 2000);
                }
            } catch (err) {
                console.error("ShieldAI API Error", err);
                showToast("⚠️ API Error! Cannot verify prompt.", "blocked");
            }
        }
    }
}, true); // Important: true means capture phase

// Also intercept clicks on buttons that might be 'Send' buttons to prevent bypassing
document.addEventListener('click', async function(e) {
    if (isReplayingEvent) return;
    
    // Check if the click is on a button or SVG inside a button (common for ChatGPT send arrow)
    const btn = e.target.closest('button');
    if (btn) {
        // Is there a textarea nearby? Let's just blindly check the most active/closest textarea.
        const textAreas = document.querySelectorAll('textarea, [contenteditable="true"]');
        let promptText = "";
        
        // Find the one with text
        for (let target of textAreas) {
            let t = target.value || target.innerText;
            if (t && t.trim().length > 0) {
                promptText = t;
                break;
            }
        }

        // If no prompt text found, let the click pass (might be an unrelated button)
        if (!promptText.trim()) return;

        // Optionally, pause and scan for button clicks too.
        // It's harder with buttons because it's hard to know which textarea it belongs to, 
        // but since most people hit "Enter" on LLMs, the keyboard block is most effective.
    }
}, true);
