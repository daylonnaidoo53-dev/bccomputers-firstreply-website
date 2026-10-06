# 00 — Workspace Manifest: Project FirstReply PC Recon

**Author:** Daylon Naidoo & Antigravity CCCO  
**Workspace Root:** `c:\Users\brooc\Documents\AI Framework\BCComputers-AI-Workspace`  
**Date:** 2026-10-06  
**Status:** COMPLETE (Ground Truth Verified)

---

## 1. Complete File Tree

```
c:\Users\brooc\Documents\AI Framework\BCComputers-AI-Workspace
├── .env.example                     # Environment template for cloud/external keys
├── .firebaserc                      # Firebase project target (`bccomputers-firstreply`)
├── .gitignore                       # Git ignore list
├── AGENTS.md                        # Always-on AIOS-lite instruction set & Hard Gate rules
├── BRAIN.md                         # Context on Daylon Naidoo, BCComputers, offer, pricing
├── CLAUDE.md                        # Instructions mirror for Claude
├── GEMINI.md                        # Instructions mirror for Gemini
├── LICENSE                          # MIT License
├── README.md                        # Workspace documentation & quickstart
├── TODAY.md                         # Daily focus & active tasks ledger
├── firebase.json                    # Firebase hosting rewrites & firestore configuration
├── firestore.indexes.json           # Firestore index definitions
├── firestore.rules                  # Firestore security rules (quote requests)
├── index.html                       # BCComputers First-Reply marketing website
├── progress.md                      # Operational progress ledger
├── css/
│   └── styles.css                   # Styles for the marketing website
├── js/
│   ├── firebase-config.js           # Firebase app initialization
│   ├── main.js                      # Mobile nav, smooth scroll, FAQ toggles
│   └── quote-form.js                # Quote request form submit to Firestore
├── scripts/
│   ├── rename-workspace.bat         # Workspace naming utility
│   └── serve.cjs                    # Dependency-free Node.js static preview server
├── directives/
│   ├── _INDEX.md                    # Playbook library index
│   ├── build_loop_lite.md           # Disciplined plan-implement-review-verify cycle
│   ├── client_message_draft.md      # Draft-only message rules
│   ├── daily_sheet.md               # Daily sheet management routine
│   └── onboard_new_client.md        # Client onboarding protocol (5 phases)
├── templates/
│   ├── daily-sheet.md               # Daily sheet template
│   ├── playbook.md                  # Standard playbook template
│   ├── project-AGENTS.md            # Sub-project agent instructions template
│   └── session-pickup.md            # Session handoff note template
├── execution/
│   ├── README.md                    # Script execution instructions
│   └── example_new_day.py           # TODAY.md generation script
├── drafts/
│   └── README.md                    # Storage for unapproved drafts
└── first-reply/                     # Existing backend service (Fitness Fuzion)
    ├── .env.example                 # Service environment template
    ├── .gitignore                   # Service git ignore
    ├── README.md                    # Service architectural documentation & guide
    ├── config.py                    # Typed Pydantic/dataclass configuration loader
    ├── config.yaml                  # Local business facts, slots, and SLA rules
    ├── database.py                  # SQLite schema (`leads`, `senders`) & data operations
    ├── demo.ps1                     # PowerShell test runner
    ├── demo.sh                      # Shell test runner
    ├── handoff.py                   # Owner alerting and TAKE takeover management
    ├── live_demo.py                 # 12-step interactive end-to-end pipeline simulator
    ├── main.py                      # FastAPI app entrypoint with lifespan startup
    ├── reply.py                     # Deterministic reply generator & LLM whitelist validator
    ├── requirements.txt             # Service dependencies (FastAPI, uvicorn, httpx, etc.)
    ├── app/
    │   ├── __init__.py
    │   ├── adapters/
    │   │   ├── __init__.py
    │   │   ├── base.py              # InboundMessage dataclass & BaseAdapter interface
    │   │   ├── email.py             # IMAP/webhook email adapter stub
    │   │   ├── email_util.py        # Asynchronous aiosmtplib dispatch helper
    │   │   ├── form.py              # Website contact form adapter
    │   │   ├── instagram.py         # Instagram DM adapter stub
    │   │   └── whatsapp.py          # WhatsApp Cloud API adapter with HMAC verification
    │   └── routes/
    │       ├── __init__.py
    │       ├── admin.py             # Admin endpoints (`/admin/leads`, `/admin/leads.csv`)
    │       └── webhooks.py          # Inbound webhook ingestion (`/webhook/{channel}`)
    └── tests/
        ├── test_admin.py            # Admin token & data access tests
        ├── test_handoff.py          # Owner notification & TAKE tests
        ├── test_optout.py           # POPIA STOP opt-out tests
        ├── test_reply.py            # Deterministic template & LLM fact check tests
        ├── test_sla.py              # 120s response SLA measurement tests
        └── test_webhook_sig.py      # HMAC signature validation tests
```

---

## 2. Purpose of Each Major Component

| Component | Location | Role & Purpose |
|---|---|---|
| **Workspace Governance** | `AGENTS.md`, `BRAIN.md`, `TODAY.md` | Single source of truth for Daylon Naidoo, the AIOS-lite Hard Gate, brand values, client profiles, and daily goals. |
| **Directives & Procedures** | `directives/` | Standard Operating Procedures (SOPs) for onboarding clients, building code with tests (`build_loop_lite.md`), and drafting messages. |
| **Marketing Website** | `index.html`, `css/`, `js/` | Live customer-facing landing page deployed to Firebase Hosting (`https://bccomputers-firstreply.web.app`) for lead capture in Paarl. |
| **Fitness Fuzion First-Reply Engine** | `first-reply/` | Cloud-hosted FastAPI inbound webhook daemon responding to WhatsApp and web form leads under 120s. |
| **FirstReply PC System (New)** | Target: `firstreply_pc/` & `docs/` | Desktop-native, local-first PC application providing instant AI replies to any highlighted text, email, or chat on PC without fees or paid API keys. |

---

## 3. Existing Workflows, Components & Data Models

### 3.1 Data Models (in `first-reply/database.py`)
- **`leads` Table**:
  - `id`: Auto-incrementing primary key.
  - `channel`: `whatsapp`, `form`, `email`, `instagram`.
  - `sender_id`: Phone number / email identifier.
  - `sender_name`: Contact name.
  - `text`: Inbound query body.
  - `received_at`: UTC timestamp.
  - `reply_text`: Generated reply draft or sent message.
  - `reply_sent_at`: Timestamp of reply dispatch.
  - `replied_within_sla`: Binary flag (under 120 seconds).
  - `owner_took_over_at`: Timestamp when human owner executed `TAKE`.
  - `bot_on`: Active reply toggle.
  - `opted_out`: POPIA opt-out toggle (triggered by `STOP`).
  - `auto_reply_sent`: Frequency limiter (1 auto-reply per 24 hours).
- **`senders` Table**:
  - Tracks unique contact status, takeover state, and opt-out preferences.

### 3.2 Existing Workflows
1. **Inbound Webhook** (`/webhook/{channel}`):
   - HMAC payload signature verification.
   - Channel adapter standardizes payload to `InboundMessage`.
   - POPIA opt-out check: if message contains `STOP`, set `opted_out = 1`.
   - Takeover check: if owner took over or messaged within 24h, silence bot.
2. **Reply Construction** (`reply.py`):
   - Strict deterministic assembly from `config.yaml` (business name, trial slots, city).
   - Optional LLM polish (`polish_reply`): validates output with `_validate_llm_output` to guarantee zero hallucinated prices, unapproved numbers, or rogue URLs.
3. **Owner Handoff** (`handoff.py`):
   - Notifies Daylon / business owner via WhatsApp / email with lead summary and draft.
   - Listens for `TAKE {id}` or `BOT ON {id}` command.
4. **Admin Inspection** (`admin.py`):
   - Bearer/Token-protected inspection endpoint returning lead history and CSV download.

---

## 4. Constraints, Unknowns & Risks

### Constraints
1. **Zero-Dollar AI Budget**:
   - Strictly no paid API keys (no billed OpenAI tokens, no Anthropic billing, etc.).
   - Core capabilities must function completely free on local PC models (Ollama, LM Studio, llama.cpp) and structured free-tier cloud endpoints (Google AI Studio Gemini Free, Groq Free Tier, OpenRouter `:free`, Cloudflare Workers AI free allowance).
2. **Hard Gate**:
   - Zero outbound messages or automated transmissions without explicit user approval. The desktop tool must draft, present, allow editing, and provide 1-click copy/insert.
3. **Local PC Environment**:
   - Running on Windows 11 (PowerShell environment, Node 26.7.0, Python 3.14.8).
   - Must handle offline scenarios cleanly with local deterministic templates.

### Unknowns & Technical Risks
1. **Local Model Availability**:
   - User's PC may or may not have Ollama installed or have high-end GPU VRAM.
   - *Mitigation*: Multi-tier quota router with local template fallbacks and instant free cloud tier fallbacks (Groq, Gemini, OpenRouter free).
2. **Global Hotkey & Selection Capture across Windows Apps**:
   - Windows security restrictions on clipboard sniffing or foreground window text extraction.
   - *Mitigation*: Lightweight global hotkey listener with clipboard reading and fallback floating quick-input bar.

---

## 5. What Can Be Reused vs What Must Be Built

| Component | Status | Action Plan |
|---|---|---|
| **Fact Validation & Whitelist Engine** (`reply.py`) | **REUSE & ADAPT** | Carry forward `_validate_llm_output` into FirstReply PC's Safety Layer to guarantee local AI never invents unauthorized numbers, prices, or links. |
| **Deterministic Template Fallback** (`config.yaml` / `reply.py`) | **REUSE & EXPAND** | Expand into tone-based deterministic templates for 100% offline or quota-exhausted operation. |
| **SQLite Persistence & History** (`database.py`) | **REUSE & EXTEND** | Extend schema to support `conversations`, `drafts`, `quota_ledgers`, `tone_profiles`, and `prompt_traces`. |
| **Local Preview Server** (`serve.cjs`) | **REUSE & ENHANCE** | Provide lightweight previewing and zero-dependency local dev serving. |
| **Capture Layer (Hotkey & Selection)** | **BUILD NEW** | Windows/cross-platform global capture daemon and clipboard reader. |
| **Quota-Aware Model Router** | **BUILD NEW** | Intelligent router querying Local Ollama -> Groq Free -> Gemini Free -> OpenRouter Free -> Local Templates with live quota budgeting (max 256 output tokens). |
| **Tone Profiler & Context Engine** | **BUILD NEW** | Quick presets: Professional, Casual, Empathetic, Direct, Urgent/Booking, plus custom user style seeds. |
| **User UI (Floating Draft Card & Tray)** | **BUILD NEW** | Modern, instant desktop popup interface with tone switcher, live draft editor, copy/send actions, privacy indicators, and quota badge. |
| **Dev Dashboard (`/dev`)** | **BUILD NEW** | Real-time monitoring UI with task board, prompt traces, model call logs, token gauges, feature flags, and seed data. |
| **Plugin Architecture** | **BUILD NEW** | Extensible connector hooks for desktop mail (Outlook/Thunderbird), WhatsApp Web, Slack, and generic clipboard. |
