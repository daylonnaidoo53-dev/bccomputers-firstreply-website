# 01 — Gap Analysis & MVP Plan: FirstReply PC

**Author:** Daylon Naidoo & Antigravity CCCO  
**Date:** 2026-10-06  
**Status:** APPROVED FOR BUILD

---

## 1. Executive Summary & Product Vision

**FirstReply PC** is a desktop AI copilot designed for PC users (Windows / macOS / Linux) that generates the "first reply" to any message, email, or chat in under 2 seconds using **strictly zero-cost AI resources**. 

### The Core Philosophy
> *"The core system is free forever. We sell convenience, not access."*
- **100% Free for Developer & User**: No paid API accounts, no credit cards, no monthly token bills.
- **Privacy First & Local Priority**: Runs on local open-source models (Ollama / llama.cpp / LM Studio) whenever available, with zero data leaving the PC.
- **Quota-Guarded Free Cloud Fallback**: When local resources are unavailable or constrained, fall back to verified free tiers (Groq, Google Gemini Free, OpenRouter Free) with strict rate-limiting, hard cutoffs, and prompt compression.
- **Graceful Degradation**: If all quotas or networks are down, it falls back instantly to offline deterministic templating. It never crashes or stalls.
- **Human-in-the-Loop (Hard Gate)**: Drafts only. The user reviews, edits, selects tone, and copies or inserts with one keystroke.

---

## 2. Gap Analysis: Existing System vs FirstReply PC

| Capability | Existing System (`first-reply/`) | FirstReply PC Desktop System | Gap / Implementation Required |
|---|---|---|---|
| **Target Platform** | Cloud server / Webhook daemon (Render/Railway/Linux) | Local PC Desktop (Windows 11 / macOS / Linux) | Need local desktop runner, system tray icon, and global hotkey listener. |
| **Trigger Mechanism** | Passive HTTP webhooks (`/webhook/whatsapp`, `/webhook/form`) | Active user selection / Hotkey (`Ctrl+Shift+R` or clipboard poll) | Need active OS capture layer & clipboard reader. |
| **Model Architecture** | Single optional OpenAI API call (`reply.py`) | Priority Quota Router (Ollama -> Groq Free -> Gemini Free -> OpenRouter Free -> Offline Template) | Build multi-provider adapter & quota tracker with auto-failover. |
| **Quota Management** | None (assumes billing account) | Active quota ledger: token budgeting, RPM/TPM caps, hard stop thresholds | Build SQLite-backed Quota Guard & real-time quota gauges. |
| **Tones & Context** | Fixed gym template from `config.yaml` | Multi-tone engine: Casual, Professional, Direct, Empathetic, Booking / Urgent | Build Tone Engine with configurable style prompts & few-shot memory. |
| **User Interface** | None (owner receives WhatsApp ping) | Modern desktop Draft Card popup: hotkey-triggered, dark/light theme, live edit, 1-click copy/insert | Build sleek User UI with status, privacy, and tone pills. |
| **Developer / Ops UI** | Static JSON `/admin/leads` | Interactive `/dev` Dashboard: live task board, prompt traces, token logs, feature flags, seed data | Build rich Dev UI for Daylon and system operators. |
| **Safety & Privacy** | Regex whitelist in `reply.py` | Expanded Safety & PII filter, local-only toggle, and privacy status indicators | Inherit and generalize regex whitelist + add PII redaction. |
| **Extensibility** | Hardcoded channel adapters | Modular desktop plugin architecture for Web WhatsApp, Desktop Mail, and Clipboard | Implement clean Plugin Interface. |

---

## 3. Architecture Blueprint

```
 ┌─────────────────────────────────────────────────────────────┐
 │                      DESKTOP USER                           │
 │      Selects text in any app -> Press Ctrl+Shift+R          │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                    CAPTURE & TRAY LAYER                     │
 │  - Global Hotkey Listener (Windows / Cross-platform)        │
 │  - Clipboard & Active Selection Capture                     │
 │  - System Tray Daemon (Status, Quick Actions, Settings)     │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │              LOCAL FASTAPI / PYTHON SIDECAR                 │
 │                                                             │
 │   ┌─────────────────────────────────────────────────────┐   │
 │   │                 CONTEXT BUILDER                     │   │
 │   │  - Cleans input message                             │   │
 │   │  - Selects tone profile (Casual / Pro / Direct)     │   │
 │   │  - Injects user profile & business facts            │   │
 │   └──────────────────────────┬──────────────────────────┘   │
 │                              │                              │
 │                              ▼                              │
 │   ┌─────────────────────────────────────────────────────┐   │
 │   │               QUOTA-AWARE MODEL ROUTER              │   │
 │   │                                                     │   │
 │   │  Tier 1: Local Ollama / llama.cpp (100% Free/Offline│   │
 │   │      ▼ [If unavailable or uninstalled]             │   │
 │   │  Tier 2: Groq Free Tier (Fastest Llama-3.3-70B/8B)  │   │
 │   │      ▼ [If quota reached or key missing]            │   │
 │   │  Tier 3: Google Gemini Free Tier (AI Studio)        │   │
 │   │      ▼ [If quota reached or key missing]            │   │
 │   │  Tier 4: OpenRouter Free Models (:free endpoints)   │   │
 │   │      ▼ [If offline or all quotas exhausted]         │   │
 │   │  Tier 5: Offline Deterministic Template Engine      │   │
 │   └──────────────────────────┬──────────────────────────┘   │
 │                              │                              │
 │                              ▼                              │
 │   ┌─────────────────────────────────────────────────────┐   │
 │   │             QUOTA GUARD & SAFETY FILTER             │   │
 │   │  - Enforces 256 max tokens output limit             │   │
 │   │  - Validates forbidden hallucinated numbers/prices  │   │
 │   │  - Logs token usage, latency, and provider trace    │   │
 │   └──────────────────────────┬──────────────────────────┘   │
 │                              │                              │
 └──────────────────────────────┼──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                    DUAL INTERFACE LAYER                     │
 │                                                             │
 │   1. USER UI (Floating Draft Card)                          │
 │      - Live Draft Preview & In-place Editing                │
 │      - Quick Tone Pills & 1-click Regenerate                │
 │      - "Copy to Clipboard" & "Insert"                       │
 │      - Privacy Status: [🟢 Local Only] / [🟡 Free Cloud]    │
 │      - Quota Meter: [⚡ 98% Free Quota Remaining]           │
 │                                                             │
 │   2. DEV DASHBOARD (/dev)                                   │
 │      - Real-Time Task Board & System Health                 │
 │      - Prompt & Token Traces with Latency waterfall         │
 │      - Provider Quota Ledgers & Cost Guard ($0.00 locked)   │
 │      - Feature Flags & Model Router Controls                │
 │      - Seed Data & Test Bench                               │
 └─────────────────────────────────────────────────────────────┘
```

---

## 4. Phased MVP Build Plan

### Phase 1: Core Engine & Quota Router (Immediate)
- Package directory: `firstreply_pc/`
- SQLite schema: `history`, `quotas`, `tones`, `traces`, `settings`.
- Quota Manager: Real-time request and token accounting per provider with stop limits.
- Model Router: Support for:
  - Local Ollama (`http://localhost:11434/v1`)
  - Groq Free (`https://api.groq.com/openai/v1`)
  - Google Gemini Free (`gemini-2.5-flash` / `gemini-1.5-flash`)
  - OpenRouter Free (`meta-llama/llama-3.2-3b-instruct:free`)
  - Offline Deterministic Template Engine.
- Context & Tone Builder: 5 built-in tone presets with customizable parameters.
- Safety Filter: Anti-hallucination whitelist regex filter.

### Phase 2: Dual User & Dev Interface (Next)
- Fast, rich desktop web interface serving:
  - User Draft Card (`/`): floating modal aesthetic, keyboard shortcuts, tone selector, copy button, privacy shield.
  - Dev Dashboard (`/dev`): live inspection of model traces, quota charts, prompt inspector, task board, and seed scenarios.
- Desktop Shell / Tray Launcher: Single-click launcher for Windows (`run_firstreply.bat` / `desktop_tray.py`).

### Phase 3: Verification, Testing & Plugin Layer
- Comprehensive pytest test suite covering router fallbacks, quota throttling, tone builders, and safety filters.
- Plugin interface for Email, WhatsApp Web, and Clipboard listeners.
- 12-step end-to-end verification script.

### Phase 4: Marketing, Docs & Monetization Strategy
- Architecture diagram & technical runbook.
- Quota & Privacy policies.
- Free monetization blueprint ("Core free forever, optional paid convenience").
- Full documentation suite in `/docs/`.
