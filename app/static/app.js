// Minimal µJS-like functionality for SSE and forms

document.addEventListener("DOMContentLoaded", () => {
    // SSE handling
    document.querySelectorAll('[u-sse]').forEach(el => {
        const url = el.getAttribute('u-sse');
        const source = new EventSource(url);
        
        source.onmessage = function(event) {
            el.innerHTML = event.data;
        };
        
        source.onerror = function() {
            console.error("SSE Connection Error to " + url);
        };
    });

    // AJAX Form submissions handling (u-post)
    document.querySelectorAll('form[u-post]').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn ? btn.textContent : '';
            if (btn) btn.textContent = 'Submitting...';
            
            const url = form.getAttribute('action') || form.getAttribute('u-post');
            const formData = new FormData(form);
            
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData
                });
                
                const resultDiv = document.querySelector(form.getAttribute('u-target')) || form.nextElementSibling || document.createElement('div');
                if (!resultDiv.parentNode && form.parentNode) {
                    form.parentNode.insertBefore(resultDiv, form.nextSibling);
                }
                
                if (response.ok) {
                    const data = await response.json();
                    resultDiv.innerHTML = `<div class="success">${data.message || 'Success!'}</div>`;
                    form.reset();
                } else {
                    const error = await response.json();
                    resultDiv.innerHTML = `<div class="error" style="color:red; margin-top:10px;">${error.detail || 'An error occurred'}</div>`;
                }
            } catch (err) {
                console.error(err);
                alert("Network error occurred.");
            } finally {
                if (btn) btn.textContent = originalText;
            }
        });
    });
});
