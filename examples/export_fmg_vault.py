"""Import an Azgaar FMG full export and write an Obsidian-compatible Markdown vault."""

from __future__ import annotations

import argparse
from pathlib import Path

from worldloom.convert import convert


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to an FMG full JSON export")
    parser.add_argument("output", type=Path, help="Output Markdown vault directory")
    args = parser.parse_args()

    convert("fmg", "markdown-vault", [args.input], args.output)
    print(f"Wrote Markdown vault to {args.output}")


if __name__ == "__main__":
    main()
