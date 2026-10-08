"""Report function size, cyclomatic complexity, and nesting under src/.

This is an informational audit. It does not enforce thresholds or change source.
Run: python scripts/audit_src_complexity.py --output src-complexity-audit.md
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _nesting_depth(node: ast.AST, depth: int = 0) -> int:
    """Return maximum nested control-flow depth within a function."""
    controls = (
        ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With,
        ast.AsyncWith, ast.Match, ast.ExceptHandler,
    )
    children_depth = depth + 1 if isinstance(node, controls) else depth
    return max(
        [children_depth]
        + [_nesting_depth(child, children_depth) for child in ast.iter_child_nodes(node)]
    )


def _function_nesting(path: Path) -> dict[tuple[str, int, str], int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[tuple[str, int, str], int] = {}

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            found[(str(path), node.lineno, node.name)] = _nesting_depth(node)
            self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

    Visitor().visit(tree)
    return found


def _run_radon() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-m", "radon", "cc", "-s", "-j", "src"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def build_report() -> str:
    files = sorted(Path("src").rglob("*.py"))
    if not files:
        raise SystemExit("No Python files found under src/")
    complexity = _run_radon()
    nesting: dict[tuple[str, int, str], int] = {}
    for path in files:
        nesting.update(_function_nesting(path))

    functions: list[dict[str, Any]] = []
    for filename, blocks in complexity.items():
        for block in blocks:
            if block.get("type") not in {"function", "method"}:
                continue
            line_start = int(block["lineno"])
            line_end = int(block.get("endline") or line_start)
            key = (filename, line_start, str(block["name"]))
            functions.append({
                "file": filename,
                "name": block["name"],
                "start": line_start,
                "lines": line_end - line_start + 1,
                "complexity": int(block["complexity"]),
                "nesting": nesting.get(key, 0),
                "rank": block.get("rank", "?"),
            })

    total_lines = sum(len(path.read_text(encoding="utf-8").splitlines()) for path in files)
    output = [
        "# Source function-size and complexity baseline",
        "",
        "> Informational snapshot only. No thresholds are enforced and no refactoring is implied.",
        "",
        "## Scope",
        "",
        f"- Python files under src/: {len(files)}",
        f"- Total source lines (including comments and blank lines): {total_lines}",
        f"- Functions and methods measured by Radon: {len(functions)}",
        "- Cyclomatic complexity: Radon CC score; higher values indicate more independent control-flow paths.",
        "- Function lines: inclusive source span from the function's first to last line, including nested definitions.",
        "- Nesting: maximum nested control-flow constructs in the function body; a supplementary AST measure.",
        "",
        "## Highest cyclomatic complexity",
        "",
        "| Function | File:line | Lines | CC | Nesting | Radon rank |",
        "|---|---|---:|---:|---:|---|",
    ]
    for item in sorted(functions, key=lambda x: (-x["complexity"], x["file"], x["start"]))[:30]:
        output.append(
            f"| {item['name']} | {item['file']}:{item['start']} | "
            f"{item['lines']} | {item['complexity']} | {item['nesting']} | {item['rank']} |"
        )
    output.extend([
        "",
        "## Longest functions and methods",
        "",
        "| Function | File:line | Lines | CC | Nesting | Radon rank |",
        "|---|---|---:|---:|---:|---|",
    ])
    for item in sorted(functions, key=lambda x: (-x["lines"], -x["complexity"], x["file"], x["start"]))[:30]:
        output.append(
            f"| {item['name']} | {item['file']}:{item['start']} | "
            f"{item['lines']} | {item['complexity']} | {item['nesting']} | {item['rank']} |"
        )
    output.extend([
        "",
        "## Interpretation notes",
        "",
        "- Rankings are triage aids, not quality judgements or refactoring instructions.",
        "- Long sequential functions may be straightforward; short functions may still be difficult to reason about.",
        "- Complexity scores do not capture mixed responsibilities, naming, domain difficulty, or test adequacy.",
        "- The nesting metric counts nested control-flow constructs and is supplementary; it is not a standard Radon metric.",
        "- This snapshot is tied to the exact commit tested by the workflow. Re-run after source changes before comparing baselines.",
        "",
    ])
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("src-complexity-audit.md"))
    args = parser.parse_args()
    report = build_report()
    args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
