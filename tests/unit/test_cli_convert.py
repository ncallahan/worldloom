from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.cli import main
from worldloom.core import WorldState
from worldloom.core.persistence import load_world


ROOT = Path(__file__).parents[2]
THIMALAND = ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _run(args, capsys):
    code = main(["convert", *map(str, args)])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _minimal_fmg(path: Path, version: str) -> None:
    path.write_text(
        json.dumps(
            {
                "info": {"version": version, "mapId": "minimal", "seed": 1},
                "pack": {"cells": [{"i": 0, "f": 0, "biome": 0, "g": -1}]},
            }
        ),
        encoding="utf-8",
    )


def test_fmg_to_markdown_vault_reports_summary_and_notes(tmp_path, capsys):
    output = tmp_path / "vault"
    code, stdout, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(THIMALAND), "-o", str(output)],
        capsys,
    )

    assert code == 0
    assert stderr == ""
    assert (output / ".worldloom-vault.json").is_file()
    assert (output / "index.md").is_file()
    assert "entities=" in stdout
    assert "notes=" in stdout
    assert "summary:" in stdout


def test_multiple_inputs_use_stems_and_duplicate_stems_abort(tmp_path, capsys):
    second = tmp_path / "Second Map.json"
    shutil.copyfile(THIMALAND, second)
    output = tmp_path / "out"

    code, stdout, stderr = _run(
        [
            "-f",
            "fmg",
            "-t",
            "markdown-vault",
            str(THIMALAND),
            str(second),
            "-o",
            str(output),
        ],
        capsys,
    )

    assert code == 0
    assert stderr == ""
    assert (output / "Thimaland_Full_2026-10-02-14-17").is_dir()
    assert (output / "Second_Map").is_dir()
    assert stdout.count("summary:") == 2

    left = tmp_path / "same!.json"
    right = tmp_path / "same?.json"
    left.write_bytes(b"not imported")
    right.write_bytes(b"not imported")
    duplicate_output = tmp_path / "duplicate"
    code, _, stderr = _run(
        [
            "-f",
            "fmg",
            "-t",
            "markdown-vault",
            str(left),
            str(right),
            "-o",
            str(duplicate_output),
        ],
        capsys,
    )
    assert code == 1
    assert "duplicate output stem" in stderr
    assert not duplicate_output.exists()


def test_world_json_roundtrip_matches_direct_markdown_projection(tmp_path, capsys):
    direct = tmp_path / "direct"
    intermediate = tmp_path / "world.json"
    roundtrip = tmp_path / "roundtrip"

    code, _, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(THIMALAND), "-o", str(direct)],
        capsys,
    )
    assert code == 0
    assert stderr == ""

    code, _, stderr = _run(
        ["-f", "fmg", "-t", "world-json", str(THIMALAND), "-o", str(intermediate)],
        capsys,
    )
    assert code == 0
    assert stderr == ""

    code, _, stderr = _run(
        [
            "-f",
            "world-json",
            "-t",
            "markdown-vault",
            str(intermediate),
            "-o",
            str(roundtrip),
        ],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    assert _tree_bytes(direct) == _tree_bytes(roundtrip)

    imported = WorldState()
    import_fmg_snapshot(imported, THIMALAND)
    restored = load_world(intermediate)
    def payload(world):
        return {
            "entities": world.entities,
            "fields": world.fields,
            "observations": world.observations,
        }
    assert restored.fingerprint(payload(restored)) == imported.fingerprint(
        payload(imported)
    )


def test_list_formats_and_request_validation(tmp_path, capsys):
    code = main(["convert", "--list-formats"])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    assert "fmg: source" in captured.out
    assert "world-json: source/target" in captured.out
    assert "markdown-vault: target" in captured.out

    output = tmp_path / "unused"
    code, _, stderr = _run(
        ["-f", "not-a-format", "-t", "markdown-vault", str(THIMALAND), "-o", str(output)],
        capsys,
    )
    assert code == 1
    assert "unknown source format" in stderr
    assert not output.exists()

    code, _, stderr = _run(
        ["-f", "world-json", "-t", "not-a-format", str(THIMALAND), "-o", str(output)],
        capsys,
    )
    assert code == 1
    assert "unknown target format" in stderr
    assert not output.exists()

    code, _, stderr = _run(
        ["-f", "world-json", "-t", "world-json", str(THIMALAND), "-o", str(output)],
        capsys,
    )
    assert code == 1
    assert "not supported" in stderr
    assert not output.exists()

    code, _, stderr = _run(
        [
            "-f",
            "fmg",
            "-t",
            "world-json",
            "--overwrite-edited",
            str(THIMALAND),
            "-o",
            str(output),
        ],
        capsys,
    )
    assert code == 1
    assert "only valid with markdown-vault" in stderr

    existing = tmp_path / "existing.json"
    existing.write_text("original", encoding="utf-8")
    code, _, stderr = _run(
        ["-f", "fmg", "-t", "world-json", str(THIMALAND), "-o", str(existing)],
        capsys,
    )
    assert code == 1
    assert "refusing to overwrite" in stderr
    assert existing.read_text(encoding="utf-8") == "original"

    code, _, stderr = _run(
        [
            "-f",
            "fmg",
            "-t",
            "world-json",
            "--force",
            str(THIMALAND),
            "-o",
            str(existing),
        ],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    assert json.loads(existing.read_text(encoding="utf-8"))


def test_spaces_in_paths(tmp_path, capsys):
    source = tmp_path / "source with spaces.json"
    output = tmp_path / "output with spaces" / "vault"
    shutil.copyfile(THIMALAND, source)

    code, _, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(source), "-o", str(output)],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    assert (output / "index.md").is_file()


def test_missing_and_invalid_inputs_leave_no_output(tmp_path, capsys):
    missing_output = tmp_path / "missing-output"
    code, _, stderr = _run(
        [
            "-f",
            "fmg",
            "-t",
            "markdown-vault",
            str(tmp_path / "one.json"),
            str(tmp_path / "two.json"),
            "-o",
            str(missing_output),
        ],
        capsys,
    )
    assert code == 1
    assert stderr.count("error:") == 2
    assert "Traceback" not in stderr
    assert not missing_output.exists()

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not json", encoding="utf-8")
    invalid_output = tmp_path / "invalid-output"
    code, _, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(invalid), "-o", str(invalid_output)],
        capsys,
    )
    assert code == 1
    assert "not valid JSON" in stderr
    assert "Traceback" not in stderr
    assert not invalid_output.exists()


def test_vault_safety_and_deterministic_rerun(tmp_path, capsys):
    output = tmp_path / "vault"
    code, _, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(THIMALAND), "-o", str(output)],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    original = _tree_bytes(output)

    code, _, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(THIMALAND), "-o", str(output)],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    assert _tree_bytes(output) == original

    edited = output / "index.md"
    edited.write_text(
        edited.read_text(encoding="utf-8") + "\nmanual edit\n",
        encoding="utf-8",
    )
    code, _, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(THIMALAND), "-o", str(output)],
        capsys,
    )
    assert code == 1
    assert "Hand-edited generated file" in stderr

    code, _, stderr = _run(
        [
            "-f",
            "fmg",
            "-t",
            "markdown-vault",
            "--overwrite-edited",
            str(THIMALAND),
            "-o",
            str(output),
        ],
        capsys,
    )
    assert code == 0
    assert stderr == ""

    nonempty = tmp_path / "nonempty"
    nonempty.mkdir()
    (nonempty / "keep.txt").write_text("keep", encoding="utf-8")
    code, _, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(THIMALAND), "-o", str(nonempty)],
        capsys,
    )
    assert code == 1
    assert "non-empty vault without" in stderr
    assert (nonempty / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_quiet_keeps_summary_but_suppresses_stage_output(tmp_path, capsys):
    output = tmp_path / "vault"
    code, stdout, stderr = _run(
        [
            "-f",
            "fmg",
            "-t",
            "markdown-vault",
            "--quiet",
            str(THIMALAND),
            "-o",
            str(output),
        ],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    assert "summary:" in stdout
    assert "read " not in stdout
    assert "write " not in stdout


def test_fmg_version_notice(tmp_path, capsys):
    source = tmp_path / "minimal.json"
    _minimal_fmg(source, "9.9.9")
    output = tmp_path / "vault"

    code, stdout, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(source), "-o", str(output)],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    assert "fmg_version=9.9.9" in stdout
    assert "notice: FMG version 9.9.9 differs from tested 1.153.1" in stdout

    quiet_output = tmp_path / "quiet"
    code, stdout, stderr = _run(
        [
            "-f",
            "fmg",
            "-t",
            "markdown-vault",
            "--quiet",
            str(source),
            "-o",
            str(quiet_output),
        ],
        capsys,
    )
    assert code == 0
    assert "notice:" not in stdout


def test_stage_timings_are_numeric(tmp_path, capsys):
    output = tmp_path / "vault"
    code, stdout, stderr = _run(
        ["-f", "fmg", "-t", "markdown-vault", str(THIMALAND), "-o", str(output)],
        capsys,
    )
    assert code == 0
    assert stderr == ""
    assert "read " in stdout and "s;" in stdout
    assert "write " in stdout and "s;" in stdout


def test_console_script_lists_formats():
    completed = subprocess.run(
        ["worldloom", "convert", "--list-formats"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "fmg: source" in completed.stdout
    assert completed.stderr == ""
