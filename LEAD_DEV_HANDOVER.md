# Project FirstReply PC — Lead Developer Architecture & Handover Package

> **Prepared for:** Lead Developer  
> **Executive Sponsor:** Daylon Naidoo · BCComputers  
> **System:** FirstReply PC v1.0  
> **Constraint:** 100% Free Forever. Zero Paid APIs. Strict Hard Gate for Outbound Client Messages.

---

## 1. Executive Summary

FirstReply PC is a local-first, quota-aware AI "first reply" system for PC desktop environments. It allows business owners and operators to draft, review, and automate high-conversion customer replies in seconds across **Telegram**, **Email**, **WhatsApp**, and **Website chat widgets**.

### Core Guarantees
1. **$0.00 Running Cost:** Operates exclusively using local open-source models (Ollama), generous free cloud tiers (OpenRouter, Groq, Gemini), or deterministic offline template rules.
2. **Never Drops Replies:** Cascading multi-tier router fails through gracefully down to instant offline rules if external APIs are exhausted or rate-limited.
3. **Hard Gate by Default:** Outbound messages require human review and approval unless an automated channel (like the Telegram customer bot) is explicitly toggled on by the owner.

---

## 2. Directory Structure

```
FirstReply-PC-LeadDev/
├── firstreply_pc/               # Core Python Engine & Web App
│   ├── engine/
│   │   ├── router.py            # Quota-aware multi-tier model router & fallback cascade
│   │   ├── telegram_bot.py      # Automated 24/7 Telegram customer bot (HTTP polling)
│   │   ├── database.py          # SQLite schema (history, quotas, traces, tone profiles)
│   │   ├── quota_guard.py       # 95% threshold guard, token estimator & prompt compressor
│   │   ├── safety.py            # PII redaction, prompt injection defense & output cleaner
│   │   ├── templates.py         # Deterministic offline rule engine
│   │   ├── plugins.py           # Channel formatters (Email, WhatsApp, Telegram, Clipboard)
│   │   ├── capture.py           # OS clipboard capture & hotkey interface
│   │   └── server.py            # FastAPI sidecar server (REST API + static UI server)
│   ├── ui/
│   │   ├── index.html           # Desktop User Draft Card (Glassmorphic floating quick reply)
│   │   └── dev.html             # CCCO Operations Dashboard (Live quotas, traces, bot controls)
│   ├── tests/
│   │   └── test_firstreply_pc.py # Full pytest test suite (11/11 passing tests)
│   └── desktop_tray.py          # Windows System Tray launcher daemon
├── docs/                        # Complete CCCO Architectural Specifications
│   ├── 00-workspace-manifest.md # Codebase audit and manifest
│   ├── 01-gap-analysis-and-mvp-plan.md # Architectural gap analysis & MVP roadmap
│   ├── 02-architecture-and-router.md   # Model router cascading specification
│   ├── 03-quota-and-privacy-policy.md  # Quota limits, privacy policy & compliance
│   ├── 04-runbook-and-demo-script.md   # Step-by-step developer runbook & verification
│   └── 05-marketing-and-monetization.md # Zero-cost positioning & optional commercial model
├── requirements.txt             # Exact Python dependencies
├── setup_environment.bat        # Automated 1-click venv creator & dependency installer
├── run_firstreply.bat           # 1-click server launcher
├── .env.example                 # Safe environment template
└── README.md                    # This document
```

---

## 3. Quick Start (Windows)

### Step 1: One-Click Environment Setup
Double-click `setup_environment.bat` or run:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Free Tier Keys (Optional)
Copy `.env.example` to `.env`:
```env
OPENROUTER_API_KEY=your_free_key_here
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
```
*(If left empty, FirstReply PC runs 100% locally using the Deterministic Offline Template Engine!)*

### Step 3: Run the Server
Double-click `run_firstreply.bat` or run:
```powershell
.\.venv\Scripts\python.exe -m uvicorn firstreply_pc.engine.server:app --host 127.0.0.1 --port 8123
```

- **User Draft Card:** Open `http://127.0.0.1:8123/`
- **CCCO Dev Dashboard:** Open `http://127.0.0.1:8123/dev`
- **Health Check:** `http://127.0.0.1:8123/api/health`

### Step 4: Run the Test Suite
```powershell
.\.venv\Scripts\pytest firstreply_pc/tests -v
```
**Current status:** `11 passed, 0 failed`.

---

## 4. Key Architectural Highlights for the Lead Dev

1. **Multi-Tier Cascade Router (`engine/router.py`):**
   - **Tier 1:** Local Ollama (`llama3.2:3b`) with 0.8s fail-fast connect probe.
   - **Tier 2:** Groq Free Tier (`llama-3.3-70b-versatile` — 14,400 req/day).
   - **Tier 3:** Google Gemini Free Tier (`gemini-2.5-flash` — 1,500 req/day).
   - **Tier 4:** OpenRouter Free Models with multi-model internal cascade:
     `google/gemma-4-31b-it:free` ➔ `nvidia/nemotron-3-super-120b-a12b:free` ➔ `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` ➔ `poolside/laguna-s-2.1:free`.
   - **Tier 5:** Deterministic Offline Template Engine (regex intent classification, zero internet required).

2. **Automated Telegram Bot (`engine/telegram_bot.py`):**
   - Built on pure async `httpx` long-polling (`getUpdates`).
   - Requires **no public IP, no port forwarding, no SSL certs, no webhooks**.
   - Listens for customer DMs, triggers Telegram's native typing status, prompts the LLM speaking as the company persona, and sends the response in 1-2 seconds.

3. **Website Embeddable Chat Widget (`/widget.js` & `/api/widget/chat`):**
   - Any website can drop in: `<script src="http://127.0.0.1:8123/widget.js"></script>` to provide customers an instant AI chat box.

4. **Zero-Overhead SQLite Database (`firstreply.db`):**
   - Tracks prompt traces, latency, token budgets, daily reset timestamps, and tone profiles.
   - Database file is auto-initialized on first launch and gitignored.
