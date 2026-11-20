# ClawBee — Open-Source AI Agent Hub

Discover, evaluate, build, and orchestrate open-source AI agents.

> **Status:** v0.1 — first public release. Brand: ClawBee. Repo: numoforge/ClawBeeAIHub.

## What it is

- **Directory** — searchable catalogue of open-source agents, frameworks,
  MCP servers, and skills, with licence, maintenance, and security fields.
- **Factory** — reproducible agent + skill generation from templates.
- **Orchestration** — sequential / parallel / hierarchical runs with
  human-in-the-loop approval, persistent checkpoints, and audit logging.
- **Providers** — model-agnostic adapter; LiteLLM Proxy as the only gateway
  in production. No hard dependency on a single proprietary provider.

## Quickstart (prototype)

```bash
python3 -m unittest discover -s tests -v
python3 -m clawbee.cli status
python3 -m clawbee.cli directory langgraph
```

No network, no API keys, no installs — stdlib-only Python 3.10+.

## Architecture

See `docs/ARCHITECTURE.md`. Primary orchestrator: LangGraph (MIT library
only). Fallback: Google ADK (Apache-2.0).

## Contributing

See `CONTRIBUTING.md`. Every change is a PR with review + green CI.
Security reports: see `SECURITY.md` — never file vulnerabilities publicly.

## Licence

Apache-2.0 (recommended; owner to confirm). See `LICENSE`.
