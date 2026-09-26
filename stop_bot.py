"""Stop a running bot from another terminal: python stop_bot.py"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from combat_bot.shutdown import request_stop, stop_file_path  # noqa: E402


def main() -> int:
    path = request_stop(ROOT)
    print(f"Stop requested: {path}")
    print("The bot exits within one loop cycle and releases its keys.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
