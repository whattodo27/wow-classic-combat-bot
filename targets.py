"""Manage the safe-target list and name templates from the terminal.

Examples::

    python targets.py add "Young Thistle Boar" "Kobold Vermin"
    python targets.py list
    python targets.py remove "Kobold Vermin"
    python targets.py clear

    # select a creature in game first, then learn its name plate:
    python targets.py learn "Young Thistle Boar"
    python targets.py templates
    python targets.py forget "Kobold Vermin"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

CONFIG = Path(__file__).parent / "combat_config.json"
TEMPLATES = Path(__file__).parent / "templates"


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def save(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def current_targets(data: dict) -> list[str]:
    policy = data.get("target_policy") or {}
    names = policy.get("allowed_names")
    return list(names) if isinstance(names, list) else []


def cmd_add(args: argparse.Namespace) -> int:
    data = load(args.config)
    policy = data.setdefault("target_policy", {})
    names = current_targets(data)
    added = []
    for name in args.names:
        cleaned = name.strip()
        if cleaned and cleaned not in names:
            names.append(cleaned)
            added.append(cleaned)
    policy["allowed_names"] = names
    save(args.config, data)
    print("added: " + (", ".join(added) if added else "(nothing new)"))
    print("current targets: " + (", ".join(names) if names else "(empty)"))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    names = current_targets(load(args.config))
    if not names:
        print("(no safe targets configured - the bot will not attack)")
        return 0
    print(f"{len(names)} safe target(s):")
    for index, name in enumerate(names, start=1):
        print(f"  {index}. {name}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    data = load(args.config)
    policy = data.setdefault("target_policy", {})
    names = current_targets(data)
    removed = [name for name in args.names if name in names]
    policy["allowed_names"] = [name for name in names if name not in removed]
    save(args.config, data)
    print("removed: " + (", ".join(removed) if removed else "(nothing)"))
    print("current targets: " + (", ".join(current_targets(data)) or "(empty)"))
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    data = load(args.config)
    data.setdefault("target_policy", {})["allowed_names"] = []
    save(args.config, data)
    print("target list cleared; the bot will not attack until you add targets")
    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    """Save the currently selected target's name plate as a template."""
    from combat_bot.bar_finder import color_ratio
    from combat_bot.capture import WindowCapture
    from combat_bot.layout import UiLayout

    data = load(args.config)
    title = str((data.get("window") or {}).get("title") or "")
    capture = WindowCapture(title)
    capture.focus()
    image = capture.capture_image()
    if image is None:
        print("ERROR: game window not found")
        return 1

    layout = UiLayout()
    crop = image.crop(layout.target_name_box(image.size))
    if color_ratio(crop, layout.target_name_color, 60) < 0.02:
        print("ERROR: no target is selected, so there is no name plate to learn.")
        print("       Select a target in game (Tab or click), then run again.")
        return 1

    args.templates.mkdir(parents=True, exist_ok=True)
    safe = args.name.strip().replace("/", "-")
    path = args.templates / f"{safe}.png"
    crop.save(path)
    print(f"saved template for {args.name!r} -> {path.name}")
    print(f"registered templates: {len(list(args.templates.glob('*.png')))}")
    return 0


def cmd_templates(args: argparse.Namespace) -> int:
    files = sorted(args.templates.glob("*.png"))
    if not files:
        print("(no templates registered)")
        print('Select a target in game, then: python targets.py learn "Name"')
        return 0
    print(f"{len(files)} template(s):")
    for file in files:
        print(f"  {file.stem}")
    return 0


def cmd_forget(args: argparse.Namespace) -> int:
    removed = []
    for name in args.names:
        path = args.templates / f"{name.strip().replace('/', '-')}.png"
        if path.exists():
            path.unlink()
            removed.append(name)
    print("removed: " + (", ".join(removed) if removed else "(nothing)"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage safe targets and name-plate templates"
    )
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--templates", type=Path, default=TEMPLATES)
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add one or more safe target names")
    add.add_argument("names", nargs="+")
    add.set_defaults(func=cmd_add)

    listing = sub.add_parser("list", help="show configured safe targets")
    listing.set_defaults(func=cmd_list)

    remove = sub.add_parser("remove", help="remove safe target names")
    remove.add_argument("names", nargs="+")
    remove.set_defaults(func=cmd_remove)

    clear = sub.add_parser("clear", help="remove every safe target")
    clear.set_defaults(func=cmd_clear)

    learn = sub.add_parser(
        "learn",
        help="save a name-plate template from the currently selected target",
    )
    learn.add_argument("name")
    learn.set_defaults(func=cmd_learn)

    templates = sub.add_parser("templates", help="list registered name templates")
    templates.set_defaults(func=cmd_templates)

    forget = sub.add_parser("forget", help="delete name templates")
    forget.add_argument("names", nargs="+")
    forget.set_defaults(func=cmd_forget)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
