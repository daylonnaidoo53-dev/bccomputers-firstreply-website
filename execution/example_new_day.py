#!/usr/bin/env python3
"""Generate today's daily sheet from the template (deterministic, zero-dependency).

Run:  python execution/example_new_day.py   (or python3 on Linux/macOS)

Creates TODAY.md at the workspace root from templates/daily-sheet.md,
stamping today's date. Will not overwrite an existing TODAY.md.
"""

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # workspace root
TEMPLATE = ROOT / "templates" / "daily-sheet.md"
TARGET = ROOT / "TODAY.md"


def main() -> None:
    if TARGET.exists():
        print(f"TODAY.md already exists ({TARGET}). Edit it, or delete it to regenerate.")
        return

    today = date.today().isoformat()
    content = TEMPLATE.read_text(encoding="utf-8").replace("<date>", today)
    TARGET.write_text(content, encoding="utf-8")
    print(f"Created {TARGET} for {today}.")
    print("Open it and fill in your ONE main thing.")


if __name__ == "__main__":
    main()
