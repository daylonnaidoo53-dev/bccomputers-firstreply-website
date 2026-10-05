# Build loop (lite)

## Purpose

Run a code build end-to-end: plan → implement → review → verify — stopping only
at the Hard Gate. Discipline becomes the default, not a memory.

## When to use

Any build with real code and a testable outcome. NOT for documents the human
wants written in their voice — those are just write.

## How

1. **Plan** — one paragraph: what + how + how you will verify. Human agrees.
2. **Implement** — small steps; write a failing test first where tests exist.
3. **Review** — reread your own diff for spec gaps and quality.
4. **Verify** — run the actual tests/build and paste the evidence. Never
   "should pass".
5. **Hard Gate** — deploys, pushes, sends, and money wait for explicit human go.

## Bounds

- Max 3 fix-laps; escalate to the human after that.
- Report verified vs unverified vs still-broken — never "all green".

## Changelog

- 2026-08-31: created for kit v1.0
