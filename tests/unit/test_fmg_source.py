from pathlib import Path

import pytest

from worldloom.adapters.fmg.source import load_fmg_source


REPO_ROOT = Path(__file__).parents[2]
THIMALAND = REPO_ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"


def test_source_hash_matches_committed_fixture():
    source = load_fmg_source(THIMALAND)
    assert source.sha256 == "d37a94173eb66d4aae73312838e9e100e43a95f1b7be7c0b6af2b3186db99423"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("[]", "top level"),
        ('{"pack":{"cells":[]}}', "info"),
        ('{"info":{}}', "pack"),
        ('{"info":{},"pack":{"cells":{}}}', "pack.cells"),
    ],
)
def test_source_validation_rejects_valid_json_with_wrong_shape(
    tmp_path: Path, content: str, message: str
):
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_fmg_source(path)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_source_rejects_nonfinite_json_constants(tmp_path: Path, constant: str):
    path = tmp_path / "nonfinite.json"
    path.write_text(
        f'{{"info":{{}}, "pack":{{"cells":[{{"h":{constant}}}]}}}}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-finite"):
        load_fmg_source(path)


def test_source_rejects_invalid_json(tmp_path: Path):
    path = tmp_path / "invalid.json"
    path.write_bytes(b"{not json")
    with pytest.raises(ValueError, match="valid JSON"):
        load_fmg_source(path)


def test_source_reads_bytes_before_parsing(tmp_path: Path):
    path = tmp_path / "source.json"
    raw = b'{"info":{},"pack":{"cells":[]}}'
    path.write_bytes(raw)
    source = load_fmg_source(path)
    assert source.raw_bytes == raw
