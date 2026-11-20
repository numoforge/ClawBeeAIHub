"""ClawBee prototype core — stdlib only, no network, no API keys.

Modules:
- schema: validation for directory entries and generated agents.
- directory: load/search/validate the JSON directory.
- providers: model-agnostic provider adapter interface (stub backend).
- factory: generate reproducible agents + skills from templates.
- orchestration: sequential/parallel/hierarchical runs with HITL + checkpoints.
- skills: Agent Skills (SKILL.md) parsing + validation.
"""

__version__ = "0.1.0"
