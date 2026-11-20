"""Agent Skills (open standard): SKILL.md parsing + validation.

Format: a folder named like the skill, containing SKILL.md with YAML
frontmatter (name <=64 chars, must match folder; description <=1024 chars)
then Markdown instructions. Progressive disclosure: frontmatter loads at
startup, body on activation, scripts/references only when called.
"""
from __future__ import annotations

import re
from pathlib import Path


class SkillError(ValueError):
    pass


def parse_skill_md(text: str) -> dict:
    if not text.startswith("---"):
        raise SkillError("SKILL.md must start with YAML frontmatter (---)")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SkillError("SKILL.md frontmatter is not closed with ---")
    front, body = parts[1], parts[2]
    meta = {}
    for line in front.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return {"frontmatter": meta, "body": body.strip()}


def validate_skill(skill_dir: Path | str) -> dict:
    d = Path(skill_dir)
    if not d.is_dir():
        raise SkillError(f"skill folder not found: {d}")
    md = d / "SKILL.md"
    if not md.exists():
        raise SkillError(f"{d}: missing SKILL.md")
    parsed = parse_skill_md(md.read_text(encoding="utf-8"))
    meta = parsed["frontmatter"]
    name = meta.get("name", "")
    desc = meta.get("description", "")
    if not name:
        raise SkillError(f"{d}: frontmatter 'name' required")
    if len(name) > 64 or not re.fullmatch(r"[a-z0-9-]+", name):
        raise SkillError(f"{d}: name must be <=64 chars, lowercase letters/numbers/hyphens")
    if name != d.name:
        raise SkillError(f"{d}: name {name!r} must match folder name {d.name!r}")
    if not desc:
        raise SkillError(f"{d}: frontmatter 'description' required")
    if len(desc) > 1024:
        raise SkillError(f"{d}: description must be <=1024 chars")
    if len(parsed["body"]) == 0:
        raise SkillError(f"{d}: SKILL.md body is empty")
    return {"name": name, "description": desc, "body_chars": len(parsed["body"]),
            "has_scripts": (d / "scripts").is_dir(), "has_references": (d / "references").is_dir()}
