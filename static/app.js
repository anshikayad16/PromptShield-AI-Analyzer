document.addEventListener('DOMContentLoaded', function() {
    const submitBtn = document.getElementById('submitPromptBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', analyzePrompt);
    }
});

async function analyzePrompt() {
    const promptInput = document.getElementById('promptInput').value.trim();
    if (!promptInput) {
        alert("Please enter a prompt first.");
        return;
    }

    const btn = document.getElementById('submitPromptBtn');
    btn.disabled = true;
    btn.innerText = 'Analyzing...';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: promptInput })
        });

        const data = await response.json();
        
        if (response.ok) {
            displayResult(data);
            // Optional: refresh page after a short delay to update logs and stats,
            // or we could append to the DOM dynamically. For simplicity, we just reload after 3s 
            // if we want full stats update, but here we just show the immediate result box.
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            alert(data.error || "An error occurred");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Failed to connect to the server.");
    } finally {
        btn.disabled = false;
        btn.innerText = 'Analyze & Send';
    }
}

function displayResult(data) {
    const resultBox = document.getElementById('resultBox');
    const statusBadge = document.getElementById('statusBadge');
    const aiResponse = document.getElementById('aiResponse');
    const layerTriggered = document.getElementById('layerTriggered');

    resultBox.classList.remove('hidden', 'safe', 'blocked');
    
    if (data.status === 'Safe') {
        resultBox.classList.add('safe');
        statusBadge.innerText = 'Safe';
        statusBadge.className = 'badge status-indicator safe';
    } else {
        resultBox.classList.add('blocked');
        statusBadge.innerText = 'Blocked';
        statusBadge.className = 'badge status-indicator blocked';
    }

    aiResponse.innerText = data.response;
    
    if (data.layer !== 'None') {
        layerTriggered.innerHTML = `<strong>Triggered Layer:</strong> ${data.layer} <br> <strong>Reason:</strong> ${data.reason}`;
    } else {
        layerTriggered.innerHTML = '';
    }
}
