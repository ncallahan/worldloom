"""Tests for the Radon complexity ratchet."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from check_complexity_ratchet import evaluate  # noqa: E402
from complexity_measurement import _qualified_names  # noqa: E402


def _tree(tmp_path: Path, source: str) -> Path:
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "src" / "sample.py").write_text(source, encoding="utf-8")
    return root


def _baseline(root: Path, functions: dict[str, int], threshold: int = 20) -> Path:
    path = root / "scripts" / "baseline.json"
    path.write_text(json.dumps({"threshold": threshold, "functions": functions}), encoding="utf-8")
    return path


def _if_function(name: str, count: int) -> str:
    body = [f"def {name}(" + ", ".join(f"v{i}" for i in range(count)) + "):"]
    body.extend(f"    if v{i}: pass" for i in range(count))
    return "\n".join(body) + "\n"


def _key(file: str, name: str) -> str:
    return f"src/{file}::{name}"


def _cc(root: Path, filename: str, name: str) -> int:
    result = subprocess.run(
        [sys.executable, "-m", "radon", "cc", "-s", "-j", "src"],
        cwd=root, check=True, capture_output=True, text=True,
    )
    report = json.loads(result.stdout)
    return next(int(block["complexity"]) for block in report[f"src/{filename}"] if block["name"] == name)


def test_passes_when_all_functions_are_within_threshold_or_baseline(tmp_path):
    root = _tree(tmp_path, "def simple(x):\n    return x\n")
    baseline = _baseline(root, {})
    _, violations, _ = evaluate(root, baseline)
    assert violations == []


def test_threshold_boundary_20_passes_and_21_fails(tmp_path):
    source = _if_function("at_twenty", 19) + _if_function("at_twenty_one", 20)
    root = _tree(tmp_path, source)
    assert _cc(root, "sample.py", "at_twenty") == 20
    assert _cc(root, "sample.py", "at_twenty_one") == 21
    _, violations, _ = evaluate(root, _baseline(root, {}))
    assert not any("at_twenty(" in item for item in violations)
    assert any("Rule 1" in item and "at_twenty_one" in item and "CC 21" in item and "allowed CC 20" in item for item in violations)


def test_new_function_above_threshold_reports_rule_one(tmp_path):
    root = _tree(tmp_path, _if_function("too_complex", 20))
    assert _cc(root, "sample.py", "too_complex") == 21
    _, violations, _ = evaluate(root, _baseline(root, {}))
    assert any("Rule 1" in item and "too_complex" in item and "src/sample.py" in item for item in violations)


def test_baselined_function_growth_reports_rule_two(tmp_path):
    root = _tree(tmp_path, _if_function("grow", 21))
    assert _cc(root, "sample.py", "grow") == 22
    _, violations, _ = evaluate(root, _baseline(root, {_key("sample.py", "grow"): 21}))
    assert any("Rule 2" in item and "CC 22" in item and "allowed CC 21" in item for item in violations)


def test_baselined_function_shrink_reports_rule_three(tmp_path):
    root = _tree(tmp_path, _if_function("shrink", 19))
    assert _cc(root, "sample.py", "shrink") == 20
    _, violations, _ = evaluate(root, _baseline(root, {_key("sample.py", "shrink"): 21}))
    assert any("Rule 3" in item and "CC 20" in item and "lower the baseline entry" in item for item in violations)


def test_missing_baseline_function_reports_rule_four(tmp_path):
    root = _tree(tmp_path, "def replacement(x):\n    return x\n")
    _, violations, _ = evaluate(root, _baseline(root, {_key("sample.py", "deleted"): 21}))
    assert any("Rule 4" in item and "deleted" in item and "function missing" in item for item in violations)


def test_class_methods_and_nested_functions_are_qualified_as_documented(tmp_path):
    root = _tree(tmp_path, """class Example:
    def method(self, flag):
        def inner(value):
            if value:
                return 1
            return 0
        return inner(flag)
""")
    names = _qualified_names(root / "src" / "sample.py")
    assert names[(2, "method")] == "Example.method"
    assert names[(3, "inner")] == "Example.method.<locals>.inner"


def test_all_violations_reported_and_output_is_deterministic(tmp_path):
    root = _tree(tmp_path, _if_function("alpha", 20) + _if_function("beta", 21))
    baseline = _baseline(root, {_key("sample.py", "missing"): 21})
    _, first, _ = evaluate(root, baseline)
    _, second, _ = evaluate(root, baseline)
    assert len(first) == 3
    assert first == second
    assert all(f"Rule {rule}" in "\\n".join(first) for rule in (1, 4))
    script = ROOT / "scripts" / "check_complexity_ratchet.py"
    outputs = [
        subprocess.run(
            [sys.executable, str(script), "--root", str(root), "--baseline", str(baseline)],
            capture_output=True, text=True,
        )
        for _ in range(2)
    ]
    assert outputs[0].stdout == outputs[1].stdout
    assert outputs[0].returncode == outputs[1].returncode == 1

def test_write_candidate_round_trips_for_same_tree(tmp_path):
    root = _tree(tmp_path, _if_function("large", 20) + "def small(x):\n    return x\n")
    baseline = _baseline(root, {})
    candidate = root / "candidate.json"
    script = ROOT / "scripts" / "check_complexity_ratchet.py"
    run = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "--baseline", str(baseline),
         "--write-candidate", str(candidate)],
        capture_output=True, text=True,
    )
    assert run.returncode == 1
    written = json.loads(candidate.read_text(encoding="utf-8"))
    assert written["threshold"] == 20
    assert written["functions"] == {_key("sample.py", "large"): 21}
    candidate_baseline = root / "scripts" / "candidate-baseline.json"
    candidate_baseline.write_text(json.dumps(written), encoding="utf-8")
    rows, violations, _ = evaluate(root, candidate_baseline)
    assert not violations
    assert next(row for row in rows if row["qualified_name"] == "large")["allowed"] == 21


def test_committed_repository_baseline_passes():
    baseline = ROOT / "scripts" / "complexity_baseline.json"
    _, violations, _ = evaluate(ROOT, baseline)
    assert violations == [], "\\n".join(violations)
