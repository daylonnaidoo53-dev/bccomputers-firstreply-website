# BRAIN — your workspace context

Last updated: 2026-10-06

## Who

- **You** — Daylon Naidoo · BCComputers. Builder of AI workspaces for local Cape Winelands businesses.
- **Your non-negotiables** — no cold outreach, drafts only, owner approves every message that goes out.

## What you're building / your business

- Offer: first-reply systems for local businesses — a useful reply within 2 minutes, then handoff to the owner.
- Niche / audience: gyms, wellness studios, and personal trainers in Paarl.

### Pricing (set 2026-10-06)

| Tier | Once-off Setup | Monthly Retainer | Notes |
|---|---|---|---|
| Starter (WA Business App) | R 1,500 | R 499/month | Owner sends reply manually |
| Standard (WA API – Auto) ⭐ | R 3,500 | R 899/month | Fully automated, recommended |
| Growth (Multi-location) | R 6,500 | R 1,499/month | Up to 3 numbers |

Optional add-ons: AI polish +R200/mo · Extra location +R299/mo · Priority support +R300/mo

Market context: Off-the-shelf SA platforms cost R299–R2,000/mo. Agency builds cost R7,500–R35,000 setup.
BCComputers sits below agency rates with direct-owner service.

## Live projects & clients

| Project | Where it lives | Status |
|---|---|---|
| Fitness Fuzion first-reply | `./first-reply/` | in progress |
| BCComputers AI Workspace Starter | `./` | live |

## Where everything lives

- `./` — workspace root (this folder)
- `./first-reply/` — the First-Reply System for Fitness Fuzion
- `./directives/` — playbooks for onboarding new businesses
- `./templates/` — project, daily sheet, and pickup templates

## Hard rules (violating these makes the work wrong)

1. Drafts only — never send client messages without the owner's explicit go.
2. Verify claims against the business's own published information before repeating them.
3. Never invent prices, hours, or promises in a first reply.

## Standing systems

- Daily sheet: `TODAY.md` (regenerate with `python execution/example_new_day.py`)
- Drafts go to: `./drafts/`
- The Hard Gate in `AGENTS.md` applies to every action.
