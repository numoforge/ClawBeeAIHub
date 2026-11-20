"""Agent factory: generate reproducible agents + skills from templates.

Reproducibility rule: same template + same inputs -> same agent.json.
No timestamps inside the generated config; generation time goes only
into HISTORY.md. No secrets in generated files, ever.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from .schema import validate_agent

AGENT_TEMPLATE = {
    "id": "",
    "name": "",
    "version": "0.1.0",
    "purpose": "",
    "framework": "langgraph",
    "model": {"adapter": "stub", "name": "stub-0"},
    "tools": [],
    "skills": [],
    "human_approval": ["publish", "spend", "delete", "share-private-data"],
    "eval": {"tasks": [], "metric": "pass^1"},
}


def generate_agent(*, agent_id: str, name: str, purpose: str,
                   framework: str = "langgraph", tools: list | None = None,
                   skills: list | None = None,
                   human_approval: list | None = None) -> dict:
    agent = copy.deepcopy(AGENT_TEMPLATE)  # never share nested template dicts
    agent.update({
        "id": agent_id,
        "name": name,
        "purpose": purpose,
        "framework": framework,
        "tools": list(tools or []),
        "skills": list(skills or []),
    })
    if human_approval is not None:
        agent["human_approval"] = list(human_approval)
    validate_agent(agent)
    return agent


def agent_fingerprint(agent: dict) -> str:
    """Deterministic SHA-256 of the canonical JSON — reproducibility check."""
    canonical = json.dumps(agent, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def write_agent(agent: dict, out_dir: Path | str, *, generated_at: str = "") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "agent.json").write_text(
        json.dumps(agent, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    history = (
        f"# {agent['name']} — History\n\n"
        f"- {agent['version']} ({generated_at or 'undated'}): "
        f"generated from template, framework={agent['framework']}, "
        f"fingerprint={agent_fingerprint(agent)[:16]}\n"
    )
    (out / "HISTORY.md").write_text(history, encoding="utf-8")
    return out / "agent.json"
