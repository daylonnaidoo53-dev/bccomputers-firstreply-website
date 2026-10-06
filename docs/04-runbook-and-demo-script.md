# 04 — Runbook & Demo Script: FirstReply PC

**Author:** Daylon Naidoo & Antigravity CCCO  
**Version:** 1.0.0  
**Date:** 2026-10-06  

---

## 1. Quickstart Runbook

### Option A: Windows 1-Click Launch
Double-click `run_firstreply.bat` in the workspace root.
This automatically initializes the database, starts the sidecar server on port `8123`, and opens the User Draft Card in your browser.

### Option B: Terminal Launch (Any OS)
```bash
# 1. Activate Python virtual environment
# Windows:
.\first-reply\.venv\Scripts\activate
# macOS/Linux:
source first-reply/.venv/bin/activate

# 2. Launch Desktop Daemon & Tray runner
python firstreply_pc/desktop_tray.py
```

### URLs:
- **User Draft Card**: `http://127.0.0.1:8123/`
- **CCCO Dev Dashboard**: `http://127.0.0.1:8123/dev`
- **REST API Specs**: `http://127.0.0.1:8123/docs`

---

## 2. Interactive End-to-End Demo Script

Follow this 5-minute walkthrough to test all features:

### Step 1: Open the User Draft Card
1. Navigate to `http://127.0.0.1:8123/`.
2. Observe the top status bar:
   - Green indicator: `Local & Free AI Active`
   - Quota status: `100% Free`
   - Cost guarantee: `$0.00 locked`
   - Hotkey hint: `Ctrl+Shift+R`

### Step 2: Test Inbound Text Capture
1. In another window (Notepad, browser, or WhatsApp Web), copy the following text:
   > *"Hi! Do you have beginner trial classes available on weekdays?"*
2. In the FirstReply PC card, click **📋 Paste Clipboard**.
3. Watch the text populate instantly.

### Step 3: Switch Voice & Tone
1. Click the **Casual (WhatsApp)** tone pill -> Notice the friendly greeting and trial offer.
2. Click **Professional (Email)** -> Observe the polite business email styling with formal sign-off.
3. Click **Direct (2 Sentences)** -> Notice the concise 1-sentence answer + 1 question format.
4. Click **Booking / Trial** -> Notice the available slots (Mon 6am, Wed 6pm, Sat 8am).

### Step 4: Human-in-the-Loop Editing & 1-Click Copy
1. Click inside the **AI First Reply Draft** text area.
2. Make a quick tweak (e.g., adding "Ask for Daylon at the front desk").
3. Click **✅ Copy & Approve** (or press `Ctrl+Enter`).
4. Paste into your chat or email window to verify the draft was placed on your clipboard.

### Step 5: Inspect the CCCO Dev Dashboard
1. Click **⚡ Dev Dashboard** in the top navigation or go to `http://127.0.0.1:8123/dev`.
2. Inspect:
   - **Metrics Strip**: Total cost locked at `$0.00`, token budget ceiling at `256`.
   - **Quota Manager**: Live progress bars showing remaining free calls for Ollama, Groq, Gemini, and OpenRouter.
   - **Prompt Traces Table**: Real-time log showing latency (e.g. `2.4ms`), token consumption, provider name, and exact prompt snippets.
   - **Test Bench**: Click any seed scenario to inject and test other client types.

---

## 3. Troubleshooting & Operations

| Issue | Root Cause | Solution |
|---|---|---|
| Port 8123 already in use | Previous server instance running | Kill the process using `netstat -ano \| findstr 8123` and `taskkill /F /PID <pid>`, or edit `SERVER_PORT` in `desktop_tray.py`. |
| "Provider failed: connection refused" | Local Ollama daemon not running | Expected if Ollama is not installed. The router automatically falls back to Free Cloud or Offline Deterministic Template Engine without breaking the user experience. |
| Output shows generic template | All cloud API keys empty & Ollama offline | This is the intended graceful degradation behavior! The offline template engine answers immediately with 0 downtime. |
