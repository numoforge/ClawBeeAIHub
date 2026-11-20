"""Agent directory: load, validate, search.

Data lives in data/directory/*.json — one file per entry, no code.
A registry listing is discovery only; this module's own vetting fields
(licence, status, security assessment) are the trust decision.
"""
from __future__ import annotations

import json
from pathlib import Path

from .schema import is_recommendable, validate_directory_entry

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "directory"


def load_directory(data_dir: Path | str = DEFAULT_DATA_DIR) -> list[dict]:
    entries, warnings = [], []
    for path in sorted(Path(data_dir).glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        warnings.extend(validate_directory_entry(entry))
        entries.append(entry)
    return entries


def search(entries: list[dict], query: str, *, recommendable_only: bool = False) -> list[dict]:
    q = query.strip().lower()
    out = []
    for e in entries:
        if recommendable_only and not is_recommendable(e):
            continue
        hay = " ".join([
            e.get("name", ""), e.get("description", ""),
            e.get("category", ""), e.get("framework", ""),
            " ".join(e.get("features", [])),
        ]).lower()
        if not q or q in hay:
            out.append(e)
    return out


def summary(entries: list[dict]) -> dict:
    return {
        "total": len(entries),
        "active": sum(1 for e in entries if e["status"] == "active"),
        "archived_or_eol": sum(1 for e in entries if e["status"] in ("archived", "eol")),
        "recommendable": sum(1 for e in entries if is_recommendable(e)),
        "osi_approved": sum(1 for e in entries if e["license"].get("osi_approved") is True),
    }
