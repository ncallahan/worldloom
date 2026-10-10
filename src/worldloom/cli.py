"""Command-line interface for Worldloom."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from worldloom.config import load_run_config
from worldloom.convert import convert, list_formats
from worldloom.runner import execute_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worldloom")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="run a simulation from a JSON configuration file",
    )
    run_parser.add_argument("config", help="path to the JSON run configuration")

    convert_parser = subparsers.add_parser(
        "convert",
        help=(
            "convert through a Worldloom world; targets such as "
            "markdown-vault are projections, not lossless source equivalents"
        ),
        description=(
            "Convert each input through a fresh Worldloom world. "
            "Projections such as markdown-vault are not lossless equivalents "
            "of their sources. world-json is a provisional, unversioned save."
        ),
    )
    convert_parser.add_argument(
        "-f", "--from", dest="source_format", help="source format"
    )
    convert_parser.add_argument(
        "-t", "--to", dest="target_format", help="target format"
    )
    convert_parser.add_argument(
        "inputs",
        nargs="*",
        help="one or more input files",
    )
    convert_parser.add_argument(
        "-o", "--output", dest="output", help="output file or directory"
    )
    convert_parser.add_argument(
        "--overwrite-edited",
        action="store_true",
        help="allow overwriting hand-edited generated Markdown files",
    )
    convert_parser.add_argument(
        "--force",
        action="store_true",
        help="allow overwriting existing world-json output files",
    )
    convert_parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress stage output but retain one summary line per input",
    )
    convert_parser.add_argument(
        "--list-formats",
        action="store_true",
        help="list available conversion formats and exit",
    )

    return parser


def _print_formats() -> None:
    for item in list_formats():
        roles = "/".join(item["roles"])
        print(f'{item["name"]}: {roles}; {item["description"]}')


def _format_entity_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{kind}={count}" for kind, count in counts.items())


def _print_result(result: dict[str, Any], *, quiet: bool) -> None:
    if not quiet:
        read_parts = [
            f"read {result['input']}: {result['read_seconds']:.3f}s",
            f"entities={_format_entity_counts(result['entity_counts'])}",
            "anomalies="
            + (
                result["anomaly_summary"]
                if result["anomaly_summary"] is not None
                else "none"
            ),
        ]
        if "fmg_version" in result:
            read_parts.append(f"fmg_version={result['fmg_version']}")
        if result.get("peak_memory") is not None:
            read_parts.append(f"peak_memory={result['peak_memory']}")
        if result.get("unrecognised_report_blocks"):
            read_parts.append(
                "unrecognised_report_blocks="
                + ",".join(result["unrecognised_report_blocks"])
            )
        print("; ".join(read_parts))

        write_parts = [
            f"write {result['output']}: {result['write_seconds']:.3f}s",
            f"bytes={result['bytes_written']}",
        ]
        if "notes_written" in result:
            write_parts.insert(1, f"notes={result['notes_written']}")
        if result.get("projection_anomalies", 0) > 0:
            write_parts.append(f"projection_anomalies={result['projection_anomalies']}")
        print("; ".join(write_parts))

        if (
            "fmg_version" in result
            and result["fmg_version"] != result["fmg_version_expected"]
        ):
            print(
                "notice: FMG version "
                f"{result['fmg_version']} differs from tested "
                f"{result['fmg_version_expected']}"
            )

    print(f"summary: {result['input']} -> {result['output']}")


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

    if args.command == "convert":
        if args.list_formats:
            _print_formats()
            return 0
        try:
            result = convert(
                args.source_format,
                args.target_format,
                args.inputs,
                args.output,
                overwrite_edited=args.overwrite_edited,
                force=args.force,
            )
        except (OSError, ValueError, NotImplementedError) as exc:
            for message in str(exc).splitlines():
                print(f"error: {message}", file=sys.stderr)
            return 1
        for item in result["results"]:
            _print_result(item, quiet=args.quiet)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
