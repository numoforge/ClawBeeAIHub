"""Validation for ClawBee directory entries and generated agents.

Stdlib only. No entry is valid without a licence field; "unknown" is a
finding, never a guess. Archived/EOL entries are valid data but must carry
a warning and must never be recommended.
"""
from __future__ import annotations

DIRECTORY_REQUIRED = [
    "id", "name", "description", "repo", "license",
    "status", "category", "languages", "features",
    "install", "maintenance", "security", "compatibility", "sources",
]
DIRECTORY_STATUSES = {"active", "archived", "eol"}
AGENT_REQUIRED = [
    "id", "name", "version", "purpose", "framework",
    "model", "tools", "skills", "human_approval", "eval",
]


class ValidationError(ValueError):
    pass


def _require(d: dict, fields, where: str) -> None:
    for f in fields:
        if f not in d or d[f] in (None, ""):
            raise ValidationError(f"{where}: missing required field '{f}'")


def validate_directory_entry(entry: dict) -> dict:
    """Validate one directory entry. Returns a warnings list (may be empty)."""
    _require(entry, DIRECTORY_REQUIRED, f"directory entry {entry.get('id', '?')}")
    if entry["status"] not in DIRECTORY_STATUSES:
        raise ValidationError(f"{entry['id']}: bad status {entry['status']!r}")
    if not isinstance(entry["repo"], dict) or "url" not in entry["repo"]:
        raise ValidationError(f"{entry['id']}: repo.url required")
    if not isinstance(entry["license"], dict) or "spdx" not in entry["license"]:
        raise ValidationError(f"{entry['id']}: license.spdx required")
    if not isinstance(entry["maintenance"], dict) or "checked_date" not in entry["maintenance"]:
        raise ValidationError(f"{entry['id']}: maintenance.checked_date required")
    if not isinstance(entry["security"], dict) or "assessment" not in entry["security"]:
        raise ValidationError(f"{entry['id']}: security.assessment required")
    if not isinstance(entry["sources"], list) or not entry["sources"]:
        raise ValidationError(f"{entry['id']}: at least one source URL required")
    warnings = []
    if entry["status"] in ("archived", "eol"):
        warnings.append(f"{entry['id']}: {entry['status']} — do not use for new builds")
    if entry["license"].get("osi_approved") is False:
        warnings.append(f"{entry['id']}: licence is not OSI-approved — check restrictions")
    if entry["license"].get("spdx") in ("UNKNOWN", "unknown"):
        warnings.append(f"{entry['id']}: licence unknown — finding, not a gap to guess")
    return warnings


def validate_agent(agent: dict) -> list:
    """Validate a generated agent config. Returns warnings."""
    _require(agent, AGENT_REQUIRED, f"agent {agent.get('id', '?')}")
    if not isinstance(agent["tools"], list):
        raise ValidationError(f"{agent['id']}: tools must be a list (MCP allow-list)")
    if not isinstance(agent["human_approval"], list):
        raise ValidationError(f"{agent['id']}: human_approval must be a list")
    if "adapter" not in agent["model"]:
        raise ValidationError(f"{agent['id']}: model.adapter required (no vendor hard-coding)")
    warnings = []
    if agent["model"].get("name") and agent["model"].get("adapter") == "stub":
        warnings.append(f"{agent['id']}: stub adapter — no live inference")
    return warnings


def is_recommendable(entry: dict) -> bool:
    """True only for active entries with a known licence."""
    return (
        entry.get("status") == "active"
        and entry.get("license", {}).get("spdx") not in (None, "", "UNKNOWN")
    )
