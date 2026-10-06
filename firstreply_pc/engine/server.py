"""
server.py — FastAPI Sidecar Server for FirstReply PC.
Coordinates model router, quota manager, capture hooks, dev metrics, and static UI.
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from firstreply_pc.engine import database
from firstreply_pc.engine.capture import CaptureLayer
from firstreply_pc.engine.plugins import format_for_channel, PLUGIN_REGISTRY
from firstreply_pc.engine.quota_guard import QuotaGuard
from firstreply_pc.engine.router import ModelRouter
from firstreply_pc.engine.telegram_bot import telegram_runner

logger = logging.getLogger(__name__)
UI_DIR = Path(__file__).resolve().parent.parent / "ui"

router_instance = ModelRouter()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan handler: initialize SQLite database and auto-start Telegram bot if configured."""
    database.init_db()
    logger.info("[FirstReply PC] Database and engine initialized successfully.")

    # Auto-start Telegram customer bot if token exists
    settings = database.get_all_settings()
    if settings.get("telegram_bot_token"):
        try:
            res = await telegram_runner.start()
            logger.info(f"[FirstReply PC] Telegram bot startup status: {res}")
        except Exception as exc:
            logger.warning(f"[FirstReply PC] Could not auto-start Telegram bot: {exc}")

    yield

    # Graceful shutdown
    if telegram_runner.is_running:
        await telegram_runner.stop()


app = FastAPI(
    title="FirstReply PC Engine",
    description="Local-first, quota-aware PC AI first-reply system.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    text: str
    tone: Optional[str] = "casual"
    channel: Optional[str] = "clipboard"
    preferred_provider: Optional[str] = None


class HistoryActionRequest(BaseModel):
    action: str  # "approve" | "copy"


class SettingUpdateRequest(BaseModel):
    key: str
    value: str


class CopyRequest(BaseModel):
    text: str


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health status and configuration."""
    quotas = database.get_all_quotas()
    settings = database.get_all_settings()
    return {
        "status": "healthy",
        "system": "FirstReply PC v1.0",
        "user": settings.get("user_name", "Daylon Naidoo"),
        "local_only": settings.get("local_only_mode", "false").lower() == "true",
        "providers_active": len([q for q in quotas if q.get("is_active")]),
    }


@app.post("/api/generate")
async def generate_reply_endpoint(req: GenerateRequest) -> Dict[str, Any]:
    """Generate a first reply for the provided message text."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    settings = database.get_all_settings()
    result = await router_instance.generate_reply(
        inbound_text=req.text.strip(),
        tone_slug=req.tone or settings.get("default_tone", "casual"),
        channel=req.channel or "clipboard",
        preferred_provider=req.preferred_provider,
    )

    # Format draft via channel plugin if applicable
    formatted_reply = format_for_channel(
        channel=req.channel or "clipboard",
        draft=result["reply"],
        metadata={"user_name": settings.get("user_name"), "business_name": settings.get("business_name")},
    )
    result["formatted_reply"] = formatted_reply
    return result


@app.get("/api/history")
async def get_history(limit: int = 50) -> Dict[str, Any]:
    """Retrieve recent reply history."""
    items = database.get_recent_history(limit=limit)
    return {"history": items}


@app.post("/api/history/{history_id}/action")
async def update_history_status(history_id: int, req: HistoryActionRequest) -> Dict[str, Any]:
    """Record copy or approval action on history item."""
    database.mark_history_action(history_id, req.action)
    return {"success": True, "history_id": history_id, "action": req.action}


@app.get("/api/quotas")
async def get_quotas() -> Dict[str, Any]:
    """Get real-time quota status and limits across all providers."""
    quotas = database.get_all_quotas()
    decorated = []
    for q in quotas:
        limit = q["daily_requests_limit"]
        used = q["daily_requests_used"]
        pct_used = round((used / limit) * 100, 1) if limit > 0 else 0
        decorated.append({
            **q,
            "pct_used": min(100.0, pct_used),
            "remaining_requests": max(0, limit - used),
            "status": "Available" if QuotaGuard.is_provider_available(q)[0] else "Throttled / Near Limit",
        })
    return {"quotas": decorated}


@app.get("/api/traces")
async def get_traces(limit: int = 30) -> Dict[str, Any]:
    """Get prompt execution traces for /dev dashboard."""
    traces = database.get_recent_traces(limit=limit)
    return {"traces": traces}


@app.get("/api/tones")
async def get_tones() -> Dict[str, Any]:
    """Get available tone profiles."""
    tones = database.get_tone_profiles()
    return {"tones": tones}


@app.get("/api/settings")
async def get_settings() -> Dict[str, Any]:
    """Get all settings (masks sensitive API keys in display)."""
    settings = database.get_all_settings()
    safe_settings = {}
    for k, v in settings.items():
        if "key" in k and v:
            safe_settings[k] = v[:4] + "..." + v[-4:] if len(v) > 8 else "***"
        else:
            safe_settings[k] = v
    return {"settings": safe_settings, "raw_keys_present": {k: bool(v) for k, v in settings.items() if "key" in k}}


@app.post("/api/settings")
async def update_setting(req: SettingUpdateRequest) -> Dict[str, Any]:
    """Update a specific setting."""
    database.update_setting(req.key, req.value)
    return {"success": True, "key": req.key}


@app.get("/api/capture/clipboard")
async def read_clipboard() -> Dict[str, Any]:
    """Read the current OS clipboard content."""
    text = CaptureLayer.get_clipboard_text()
    return {"text": text, "length": len(text)}


@app.post("/api/capture/copy")
async def write_clipboard(req: CopyRequest) -> Dict[str, Any]:
    """Copy text to the OS clipboard."""
    ok = CaptureLayer.set_clipboard_text(req.text)
    return {"success": ok}


# ── Telegram Connector Endpoints ─────────────────────────────────────────────

@app.get("/api/telegram/status")
async def telegram_status() -> Dict[str, Any]:
    """Check Telegram bot status and verify token."""
    check = await telegram_runner.verify_bot()
    return {
        "running": telegram_runner.is_running,
        "configured": bool(telegram_runner.get_token()),
        "bot_info": check,
    }


@app.post("/api/telegram/start")
async def telegram_start() -> Dict[str, Any]:
    """Start the Telegram bot background listener."""
    return await telegram_runner.start()


@app.post("/api/telegram/stop")
async def telegram_stop() -> Dict[str, Any]:
    """Stop the Telegram bot background listener."""
    return await telegram_runner.stop()


# ── Website Chat Widget / Webhook Automation ──────────────────────────────────

class WidgetChatRequest(BaseModel):
    message: str
    customer_name: Optional[str] = "Visitor"
    tone: Optional[str] = "casual"


@app.post("/api/widget/chat")
async def website_chat_widget(req: WidgetChatRequest) -> Dict[str, Any]:
    """
    Automated backend webhook for websites.
    Directly answers incoming website inquiries acting as the company persona.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    settings = database.get_all_settings()
    business_name = settings.get("business_name", "Fitness Fuzion")
    tone = req.tone or settings.get("default_tone", "casual")

    result = await router_instance.generate_reply(
        inbound_text=f"Website visitor ({req.customer_name}) asks: {req.message.strip()}",
        tone_slug=tone,
        channel="website_chat",
    )

    return {
        "success": True,
        "company": business_name,
        "reply": result.get("reply", ""),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "latency_ms": result.get("latency_ms"),
    }


@app.get("/widget.js")
async def get_embeddable_widget_script() -> HTMLResponse:
    """Return drop-in vanilla JS widget script for any website."""
    js = """
(function() {
    const host = window.FIRSTREPLY_HOST || window.location.origin;
    const container = document.createElement('div');
    container.id = 'firstreply-widget-root';
    container.innerHTML = `
        <div id="fr-bubble" style="position:fixed;bottom:24px;right:24px;width:56px;height:56px;border-radius:50%;background:#0ea5e9;color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,0.3);z-index:99999;font-size:26px;transition:transform 0.2s;">💬</div>
        <div id="fr-box" style="display:none;position:fixed;bottom:90px;right:24px;width:340px;height:450px;background:#0f172a;border:1px solid #334155;border-radius:16px;box-shadow:0 12px 36px rgba(0,0,0,0.4);z-index:99999;flex-direction:column;font-family:sans-serif;color:#f8fafc;overflow:hidden;">
            <div style="padding:14px;background:#1e293b;border-bottom:1px solid #334155;font-weight:600;display:flex;justify-content:space-between;align-items:center;">
                <span>AI Assistant · FirstReply</span>
                <span id="fr-close" style="cursor:pointer;color:#94a3b8;">✕</span>
            </div>
            <div id="fr-msgs" style="flex:1;padding:14px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;font-size:14px;">
                <div style="background:#1e293b;padding:10px 14px;border-radius:12px 12px 12px 2px;max-width:85%;">Hi there! 👋 How can we help you today? Ask about classes, memberships, or pricing!</div>
            </div>
            <div style="padding:12px;border-top:1px solid #334155;display:flex;gap:8px;">
                <input id="fr-in" placeholder="Ask a question..." style="flex:1;background:#1e293b;border:1px solid #475569;border-radius:8px;padding:8px 12px;color:#fff;outline:none;font-size:13px;" />
                <button id="fr-send" style="background:#0ea5e9;border:none;border-radius:8px;padding:8px 14px;color:#fff;cursor:pointer;font-weight:600;">Send</button>
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

    bubble.onclick = () => { box.style.display = box.style.display === 'flex' ? 'none' : 'flex'; };
    close.onclick = () => { box.style.display = 'none'; };

    async function doSend() {
        const text = input.value.trim();
        if(!text) return;
        input.value = '';
        msgs.innerHTML += `<div style="background:#0284c7;color:#fff;align-self:flex-end;padding:10px 14px;border-radius:12px 12px 2px 12px;max-width:85%;">${text}</div>`;
        msgs.scrollTop = msgs.scrollHeight;

        const loading = document.createElement('div');
        loading.style.cssText = "background:#1e293b;padding:10px 14px;border-radius:12px 12px 12px 2px;max-width:85%;color:#94a3b8;";
        loading.innerText = 'Typing...';
        msgs.appendChild(loading);
        msgs.scrollTop = msgs.scrollHeight;

        try {
            const res = await fetch(`${host}/api/widget/chat`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            loading.innerText = data.reply || "Thanks for your note! We'll follow up shortly.";
            loading.style.color = "#f8fafc";
        } catch(e) {
            loading.innerText = "Error connecting to AI service.";
        }
        msgs.scrollTop = msgs.scrollHeight;
    }

    send.onclick = doSend;
    input.onkeydown = (e) => { if (e.key === 'Enter') doSend(); };
})();
    """
    return HTMLResponse(content=js, media_type="application/javascript")


# ── Frontend HTML Routes ──────────────────────────────────────────────────────

@app.get("/")
async def serve_user_ui() -> HTMLResponse:
    """Serve the primary User UI (Floating Draft Card & Quick Reply)."""
    user_html_path = UI_DIR / "index.html"
    if user_html_path.exists():
        return HTMLResponse(content=user_html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>FirstReply PC: UI files loading...</h1>")


@app.get("/dev")
async def serve_dev_dashboard() -> HTMLResponse:
    """Serve the Dev Dashboard (Traces, Quotas, Task Board, Settings)."""
    dev_html_path = UI_DIR / "dev.html"
    if dev_html_path.exists():
        return HTMLResponse(content=dev_html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>FirstReply PC: Dev dashboard loading...</h1>")


# Mount static assets directory if it exists
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")
