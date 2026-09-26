"""Report which window each title resolves to (diagnostic only)."""
from __future__ import annotations

import pygetwindow as gw

from combat_bot.capture import find_window_by_title
from combat_bot.config import load_config
from pathlib import Path


def main() -> None:
    config = load_config(Path(__file__).parent / "combat_config.json")
    title = config.window_title
    print(f"configured title: {title!r}\n")

    print("exact matches (getWindowsWithTitle):")
    for window in gw.getWindowsWithTitle(title):
        print(
            f"  '{window.title}' left={window.left} top={window.top} "
            f"{window.width}x{window.height} minimized={window.isMinimized} active={window.isActive}"
        )

    print("\nsubstring matches (all windows):")
    for window in gw.getAllWindows():
        if window.title and title.casefold() in window.title.casefold():
            print(
                f"  '{window.title}' left={window.left} top={window.top} "
                f"{window.width}x{window.height} minimized={window.isMinimized}"
            )

    print("\nall visible windows:")
    for window in gw.getAllWindows():
        if window.title:
            print(
                f"  '{window.title}' left={window.left} top={window.top} "
                f"{window.width}x{window.height} minimized={window.isMinimized}"
            )

    print(f"\nfind_window_by_title -> {find_window_by_title(title)}")


if __name__ == "__main__":
    main()
