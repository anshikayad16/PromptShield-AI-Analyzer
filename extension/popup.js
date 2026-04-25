document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('analyzeBtn');
    const input = document.getElementById('promptInput');
    const resultArea = document.getElementById('resultArea');
    const statusBadge = document.getElementById('statusBadge');
    const reasonText = document.getElementById('reasonText');

    btn.addEventListener('click', async () => {
        const prompt = input.value.trim();
        if (!prompt) return;

        btn.disabled = true;
        btn.innerText = 'Analyzing...';
        resultArea.className = 'hidden';

        try {
            // Send request to local Flask backend
            const response = await fetch('http://127.0.0.1:5000/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: prompt })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            resultArea.className = data.status === 'Safe' ? 'safe' : 'blocked';
            statusBadge.innerText = data.status;
            
            if (data.layer !== 'None') {
                reasonText.innerText = `Detected by ${data.layer} layer: ${data.reason}`;
            } else {
                reasonText.innerText = 'Clear of known injection patterns.';
            }

        } catch (error) {
            resultArea.className = 'blocked';
            statusBadge.innerText = 'Error';
            reasonText.innerText = 'Could not connect to ShieldAI local backend. Ensure it is running on port 5000.';
        } finally {
            btn.disabled = false;
            btn.innerText = 'Analyze Prompt';
        }
    });
});
