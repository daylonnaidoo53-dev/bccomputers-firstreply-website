# execution/ — the engine layer

Scripts here are the deterministic muscle: anything that must behave the same
every single time becomes code, not agent judgment.

## Rules

1. Zero or minimal dependencies — runs on any machine (Windows, macOS, Linux).
2. No secrets in scripts — read them from `.env` if needed.
3. Scripts that call paid APIs show the cost first and wait for approval
   (the Hard Gate).
4. New script? Name it `snake_case.py`, add a docstring, update this list.

## Scripts

- `example_new_day.py` — generates today's daily sheet from the template
  (`templates/daily-sheet.md`).
  Run: `python execution/example_new_day.py` (or `python3` on Linux/macOS).
