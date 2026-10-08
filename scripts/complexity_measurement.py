"""Shared Radon measurement and function naming for audit and ratchet."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_radon(root: Path) -> dict[str, Any]:
    """Return Radon's JSON CC output for the repository's src/ tree."""
    result = subprocess.run(
        [sys.executable, "-m", "radon", "cc", "-s", "-j", "src"],
        cwd=root, check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def _qualified_names(path: Path) -> dict[tuple[int, str], str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: dict[tuple[int, str], str] = {}

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.parts: list[tuple[str, str]] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.parts.append(("class", node.name))
            self.generic_visit(node)
            self.parts.pop()

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            prefix = ".".join(name for _, name in self.parts)
            if self.parts and self.parts[-1][0] == "function":
                prefix += ".<locals>"
            qualified = f"{prefix}.{node.name}" if prefix else node.name
            names[(node.lineno, node.name)] = qualified
            self.parts.append(("function", node.name))
            self.generic_visit(node)
            self.parts.pop()

        visit_FunctionDef = _visit_function
        visit_AsyncFunctionDef = _visit_function

    Visitor().visit(tree)
    return names


def measure_functions(root: Path) -> list[dict[str, Any]]:
    """Measure functions/methods using the exact Radon invocation used by the audit."""
    root = root.resolve()
    raw = run_radon(root)
    measured: list[dict[str, Any]] = []
    for filename, blocks in sorted(raw.items()):
        relative = Path(filename).as_posix()
        path = root / relative
        names = _qualified_names(path)
        for block in blocks:
            if block.get("type") not in {"function", "method"}:
                continue
            start = int(block["lineno"])
            name = str(block["name"])
            measured.append({
                "file": relative,
                "name": name,
                "qualified_name": names.get((start, name), name),
                "start": start,
                "complexity": int(block["complexity"]),
                "rank": block.get("rank", "?"),
            })
    return sorted(measured, key=lambda item: (
        item["file"], item["start"], item["qualified_name"]
    ))
