# FMG snapshot source loading and validation.

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class FMGSource:
    path: Path
    raw_bytes: bytes
    data: dict[str, Any]
    sha256: str

    @property
    def info(self) -> dict[str, Any]:
        return self.data["info"]

    @property
    def pack(self) -> dict[str, Any]:
        return self.data["pack"]

def load_fmg_source(path: str | Path) -> FMGSource:
    source_path = Path(path)
    raw_bytes = source_path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    try:
        value = json.loads(raw_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"FMG source is not valid JSON: {source_path}") from exc
    if not isinstance(value, dict):
        raise ValueError("FMG source top level must be a JSON object")
    if not isinstance(value.get("info"), dict):
        raise ValueError("FMG source must contain an object-valued 'info'")
    if not isinstance(value.get("pack"), dict):
        raise ValueError("FMG source must contain an object-valued 'pack'")
    if not isinstance(value["pack"].get("cells"), list):
        raise ValueError("FMG source pack.cells must be a list")
    return FMGSource(source_path, raw_bytes, value, digest)
