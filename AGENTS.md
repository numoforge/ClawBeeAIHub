# AGENTS.md — ClawBee repo guidance

- Scope: open-source AI agents, frameworks, MCP servers, skills, automation.
  Out of scope: airdrops, testnets, crypto campaigns, wallets.
- Never execute untrusted repository code in production. Sandbox only.
- Never commit secrets. Never auto-merge bot PRs.
- Tests: `cd prototype && python3 -m unittest discover -s tests -v` — keep them green.
- Every change is a PR linked to an Issue, with review + CI.
- Directory entries need a licence field; archived/EOL entries carry a warning.
