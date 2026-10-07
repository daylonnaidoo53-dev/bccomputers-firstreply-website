/**
 * FirstReply PC — Embeddable 2026 Customer Chat Widget
 * Drop-in script for any website to connect inbound visitors to FirstReply AI.
 * (C) 2026 Daylon Naidoo · BCComputers & FirstReply PC
 */
(function() {
    if (document.getElementById('firstreply-widget-root')) return;

    const host = window.FIRSTREPLY_HOST || (
        (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
            ? 'http://127.0.0.1:8123'
            : (localStorage.getItem('firstreply_api_host') || window.location.origin)
    );

    const title = window.FIRSTREPLY_TITLE || "FirstReply AI Assistant";
    const greeting = window.FIRSTREPLY_GREETING || "Hi there! 👋 How can we help you today? Ask about services, hours, or instant quotes!";
    const primaryColor = window.FIRSTREPLY_COLOR || "#3b82f6";

    const container = document.createElement('div');
    container.id = 'firstreply-widget-root';
    container.innerHTML = `
        <div id="fr-bubble" style="position:fixed;bottom:24px;right:24px;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg, ${primaryColor}, #06b6d4);color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 10px 28px rgba(37,99,235,0.4);z-index:99999;font-size:26px;transition:all 0.25s cubic-bezier(0.16, 1, 0.3, 1);user-select:none;" title="Chat with FirstReply AI">
            💬
        </div>
        <div id="fr-box" style="display:none;position:fixed;bottom:96px;right:24px;width:360px;max-width:calc(100vw - 32px);height:500px;max-height:calc(100vh - 120px);background:#090d16;border:1px solid rgba(255,255,255,0.12);border-radius:18px;box-shadow:0 20px 48px rgba(0,0,0,0.6);z-index:99999;flex-direction:column;font-family:'Inter', -apple-system, BlinkMacSystemFont, sans-serif;color:#f8fafc;overflow:hidden;backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);">
            <div style="padding:16px;background:linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));border-bottom:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#10b981;box-shadow:0 0 8px rgba(16,185,129,0.8);"></div>
                    <div>
                        <div style="font-weight:700;font-size:14px;letter-spacing:-0.2px;">${title}</div>
                        <div style="font-size:11px;color:#94a3b8;">Under 2-Minute Response Guarantee</div>
                    </div>
                </div>
                <button id="fr-close" style="background:transparent;border:none;color:#94a3b8;font-size:18px;cursor:pointer;padding:4px 8px;border-radius:6px;">✕</button>
            </div>
            <div id="fr-msgs" style="flex:1;padding:16px;overflow-y:auto;display:flex;flex-direction:column;gap:12px;font-size:13px;line-height:1.5;">
                <div style="background:rgba(30,41,59,0.7);border:1px solid rgba(255,255,255,0.06);padding:12px 14px;border-radius:14px 14px 14px 2px;max-width:85%;color:#e2e8f0;">
                    ${greeting}
                </div>
            </div>
            <div style="padding:12px 14px;background:rgba(15,23,42,0.8);border-top:1px solid rgba(255,255,255,0.08);display:flex;gap:8px;align-items:center;">
                <input id="fr-in" placeholder="Ask a question..." style="flex:1;background:rgba(30,41,59,0.8);border:1px solid rgba(255,255,255,0.12);border-radius:10px;padding:10px 14px;color:#fff;outline:none;font-size:13px;font-family:inherit;" />
                <button id="fr-send" style="background:${primaryColor};border:none;border-radius:10px;padding:10px 16px;color:#fff;cursor:pointer;font-weight:600;font-size:13px;display:flex;align-items:center;gap:4px;transition:opacity 0.2s;">
                    <span>Send</span>
                </button>
            </div>
            <div style="padding:4px 12px 6px;text-align:center;font-size:10px;color:#64748b;background:rgba(15,23,42,0.95);border-top:1px solid rgba(255,255,255,0.02);">
                Powered by <strong>FirstReply PC</strong> · Local AI Copilot
            </div>
        </div>
    `;

    document.body.appendChild(container);

    const bubble = document.getElementById('fr-bubble');
    const box = document.getElementById('fr-box');
    const close = document.getElementById('fr-close');
    const input = document.getElementById('fr-in');
    const send = document.getElementById('fr-send');
    const msgs = document.getElementById('fr-msgs');

    bubble.onclick = () => {
        const isHidden = (box.style.display === 'none' || !box.style.display);
        box.style.display = isHidden ? 'flex' : 'none';
        if (isHidden) input.focus();
    };

    close.onclick = () => {
        box.style.display = 'none';
    };

    async function doSend() {
        const text = input.value.trim();
        if (!text) return;
        input.value = '';

        // Append user bubble
        msgs.innerHTML += `
            <div style="background:linear-gradient(135deg, ${primaryColor}, #2563eb);color:#fff;align-self:flex-end;padding:10px 14px;border-radius:14px 14px 2px 14px;max-width:85%;box-shadow:0 4px 12px rgba(37,99,235,0.25);">
                ${text.replace(/</g, "&lt;").replace(/>/g, "&gt;")}
            </div>
        `;
        msgs.scrollTop = msgs.scrollHeight;

        // Typing indicator
        const loading = document.createElement('div');
        loading.style.cssText = "background:rgba(30,41,59,0.7);border:1px solid rgba(255,255,255,0.06);padding:10px 14px;border-radius:14px 14px 14px 2px;max-width:85%;color:#94a3b8;font-size:12px;";
        loading.innerHTML = '<span>⚡ Drafting instant reply...</span>';
        msgs.appendChild(loading);
        msgs.scrollTop = msgs.scrollHeight;

        try {
            const endpoint = `${host.replace(/\/$/, '')}/api/widget/chat`;
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            if (!res.ok) throw new Error("HTTP " + res.status);
            const data = await res.json();
            const reply = data.reply || "Thanks for your note! We'll follow up with you shortly.";
            loading.innerHTML = reply.replace(/\n/g, "<br>");
            loading.style.color = "#f8fafc";
        } catch (e) {
            // Intelligent fallback when offline / static demo
            const fallbackReply = "Hi there! Thanks for reaching out. We received your enquiry and our team will get back to you within 2 minutes. You can also reach Daylon on WhatsApp at +27 83 254 2999.";
            loading.innerHTML = fallbackReply;
            loading.style.color = "#f8fafc";
        }
        msgs.scrollTop = msgs.scrollHeight;
    }

    send.onclick = doSend;
    input.onkeydown = (e) => {
        if (e.key === 'Enter') doSend();
    };
})();
