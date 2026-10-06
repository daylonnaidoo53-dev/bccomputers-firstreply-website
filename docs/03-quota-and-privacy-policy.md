# 03 — Quota & Privacy Policy: FirstReply PC

**Author:** Daylon Naidoo & Antigravity CCCO  
**Version:** 1.0.0  
**Effective Date:** 2026-10-06  

---

## 1. The Zero-Cost Guarantee

FirstReply PC was built on a foundational promise:
> **"Core AI functionality is free forever. No token charges. No subscriptions. No credit card required."**

### How We Deliver This:
1. **Local-First Architecture**: We leverage local open-source models through Ollama, LM Studio, or llama.cpp. When running locally, zero API calls are made and compute cost is $0.00.
2. **Verified Free Tiers Only**: When cloud fallbacks are enabled, FirstReply PC exclusively targets non-billed, zero-cost developer quotas (Groq, Google AI Studio, OpenRouter Free).
3. **Hard Ceiling Stop Guards**: At 95% of any daily free threshold, FirstReply PC halts usage for that provider and cascades to the next free tier or offline template. We will never automatically convert to a paid tier or incur overage fees.

---

## 2. Privacy Policy & Data Handling

### 2.1 Where Your Data Lives
- **100% Local Storage**: All reply history, prompt traces, tone profiles, and preferences are stored exclusively on your machine in a local SQLite file (`firstreply.db`).
- **Zero Telemetry Collection**: Project FirstReply PC does not run centralized telemetry, tracking cookies, or external analytics servers.

### 2.2 Privacy Modes

#### 🟢 Local-Only (Airgapped) Mode
- **Status**: Can be activated with one click in the Dev Dashboard (`/dev`) or User Settings.
- **Behavior**: External cloud endpoints are completely disabled. All draft generation executes strictly between local Ollama / llama.cpp instances and local deterministic rules.
- **Security Guarantee**: Zero bytes of text ever leave your PC.

#### 🟡 Free Cloud Fallback Mode
- **Status**: Default mode when local Ollama is not installed or offline.
- **Behavior**: Calls official free developer endpoints using your own free keys.
- **Data Protection**: Input prompts are compressed and sanitized (PII masked) before transmission. No data is shared with third-party advertisers.

---

## 3. Human Gate & Compliance (POPIA & GDPR)

- **Drafts Only**: FirstReply PC is an assistant, not an autonomous agent. It generates drafts for human review. It never auto-sends messages to your clients without your explicit click or keystroke.
- **Right to Erasure**: You can wipe your entire history at any time by clearing the local `firstreply.db` database.
- **POPIA Safe**: Inherits BCComputers' strict opt-out logic.
