# onboard_new_client

> Playbook for onboarding a new business onto the First-Reply System.
> One topic: getting a new client live from first call to first auto-reply.

## Purpose

Walk Daylon through every step to onboard a new business — from the sales call through
to their first automated WhatsApp reply — in 48 hours or less.

## When to use

- A new client has said YES and paid (or agreed to start).
- Do NOT start this playbook until the Hard Gate is cleared:
  client has confirmed they want to proceed and Daylon has approved the start.

## How

### PHASE 1 — Client Intake (Day 0, ~30 mins)

1. Send the client the **Client Intake Form** (ask them to fill in writing or do it live on call):
   - Business name (exact, as it appears on WhatsApp)
   - City / area
   - Offer name (e.g. "free trial class", "free consultation")
   - Available trial/booking slots (at least 3 options, day + time)
   - Owner's WhatsApp number (international format, e.g. +27824673870)
   - Owner's email address
   - Booking link (if they have one; leave blank if not)
   - Do they want AI-polished replies? (yes/no — requires OpenAI API key)

2. Confirm the client's WhatsApp is on the **WhatsApp Business App** (not personal).
   - If they want the full API (for automation), they need to upgrade to
     WhatsApp Business Platform via Meta Business Manager. Note this adds Meta costs.

3. Create a new folder: `./first-reply-[business-slug]/` (e.g. `first-reply-ironfit/`).

4. Copy the entire `./first-reply/` folder into the new folder.

5. Update `config.yaml` with the client's details from the intake form.

6. Create a `.env` file from `.env.example` and fill in any API keys the client provides.

### PHASE 2 — Test the Pipeline (Day 0-1, ~15 mins)

7. Run the test suite to confirm the system is clean for this client:
   ```
   .venv\Scripts\python.exe -m pytest tests/ -v
   ```
   All 27 tests must pass before going live.

8. Manually verify the auto-reply message looks correct:
   Open a Python shell in the venv and run:
   ```python
   from config import load_config
   from reply import build_reply
   cfg = load_config()
   print(build_reply("Test User", cfg))
   ```
   Read it out loud — does it sound right? Does it match exactly what the client agreed to?

9. Show the draft reply to the client for sign-off. **Do not go live without this.**

### PHASE 3 — WhatsApp Setup (Day 1, ~1-2 hrs — done with client)

10. If using the **WhatsApp Business App** (no API — simplest option):
    - The system will generate reply templates the owner copies and sends manually.
    - Set `llm_polish: false` and document the SLA expectation: owner responds within 2 mins.

11. If using the **WhatsApp Business API** (full automation):
    - Client must have a Meta Business account verified.
    - Create a WhatsApp Business Platform app in Meta Business Manager.
    - Get: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`.
    - Add these to the client's `.env` file.
    - Deploy the FastAPI app to a hosting platform (Railway, Render, or a VPS).
    - Set the webhook URL in Meta: `https://[your-domain]/webhooks/whatsapp`
    - Verify the webhook handshake passes (check logs for 200 OK).

### PHASE 4 — Go Live Checklist (Day 1-2)

12. Run tests one final time — all 27 must pass.
13. Send a test WhatsApp message TO the business number. Confirm the auto-reply arrives within SLA (120 seconds by default).
14. Confirm owner receives the handoff notification (WhatsApp or email).
15. Run the client through the owner commands:
    - `TAKE [lead_id]` — take over a conversation from the bot
    - `BOT ON [lead_id]` — hand the conversation back to the bot
    - STOP / UNSUBSCRIBE — opt-out handling (automatic)
16. Hand the client their **Owner Quick Reference Card** (see `templates/`).

### PHASE 5 — Handover & Ongoing

17. Export the admin CSV to confirm leads are being logged: `GET /admin/leads.csv`
18. Book a 15-min check-in call for Day 7.
19. Update `BRAIN.md` → Live projects table with client name and status = "live".

## Bounds

- Maximum 48 hours from intake to go-live.
- Only Daylon approves going live (Hard Gate applies).
- Never go live without the client seeing and signing off the auto-reply text.
- Never hardcode API keys — always use `.env`.

## Changelog

- 2026-10-06: created by Daylon Naidoo · BCComputers
