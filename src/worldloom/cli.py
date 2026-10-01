"""Command-line interface for Worldloom."""

from __future__ import annotations

import argparse
import sys

from worldloom.config import load_run_config
from worldloom.runner import execute_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worldloom")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="run a simulation from a JSON configuration file",
    )
    run_parser.add_argument("config", help="path to the JSON run configuration")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            config = load_run_config(args.config)
            execute_run(config)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(str(exc))

    return 0


if __name__ == "__main__":
    sys.exit(main())
