"""
app — Core First-Reply System package.
Author: Daylon Naido · BCComputers
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
import database
import handoff
import reply

__all__ = ["config", "database", "handoff", "reply"]
