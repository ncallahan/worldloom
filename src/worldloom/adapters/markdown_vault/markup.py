"""Markdown-safe value and markup helpers for the Markdown-vault projection."""

from __future__ import annotations

import json
import re
from typing import Any


def yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if type(value) in (int, float):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    return json.dumps(str(value), ensure_ascii=False)


def frontmatter(entries: list[tuple[str, Any]]) -> str:
    lines = ["---"]
    for key, value in entries:
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {yaml_value(item)}" for item in value)
        else:
            lines.append(f"{key}: {yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines)


def safe_text(value: Any, path: str = "value") -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Value at {path} is not JSON-serialisable") from exc
    longest = max((len(run) for run in re.findall(chr(96) + "+", text)), default=0)
    fence = chr(96) * (longest + 1)
    return f"{fence}{text}{fence}"


def display_text(value: str) -> str:
    return value.replace("|", r"\|").replace("[", r"\[").replace("]", r"\]")


def code_span(value: str) -> str:
    longest = max((len(run) for run in re.findall(chr(96) + "+", value)), default=0)
    fence = chr(96) * (longest + 1)
    single_line = value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
    if not single_line or single_line.startswith(chr(96)) or single_line.endswith(chr(96)):
        single_line = f" {single_line} "
    return f"{fence}{single_line}{fence}"


def text_field(value: str) -> str:
    longest = max((len(run) for run in re.findall(chr(96) + "+", value)), default=0)
    fence = chr(96) * max(3, longest + 1)
    return f"{fence}text\n{value}{'' if value.endswith(chr(10)) else chr(10)}{fence}"


def link(path: str, display: str) -> str:
    return f"[[{path.removesuffix('.md')}|{display_text(display)}]]"
