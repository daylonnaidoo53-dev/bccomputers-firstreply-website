# Directives — the playbook library

Playbooks are plain-English how-tos for the agent. Naming: `snake_case`, one topic
per file. An agent that finds a matching playbook follows it.

## Rules for playbooks

1. Start from the template (`templates/playbook.md`): Purpose / When to use /
   How / Bounds / Changelog.
2. Keep them short — if it needs a novel, split it into two playbooks.
3. After sign-off, the only allowed edit is appending a Changelog line.
   Rewriting a playbook is a human decision.

## Index

- `daily_sheet.md` — keep one page of today's focus
- `build_loop_lite.md` — disciplined build loop for real code work
- `client_message_draft.md` — draft-only client messages
- `onboard_new_client.md` — full 5-phase playbook to onboard a new business (intake → go-live)
