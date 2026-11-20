# Contributing to ClawBee

Thank you for contributing to ClawBee, the open-source AI Agent Hub.

## Ground rules

- Every piece of work starts as a GitHub Issue; every PR links its Issue.
- Work on a branch (`feature/<short>`, `fix/<short>`, `docs/<short>`). Never commit directly to `main`.
- All changes go through a Pull Request with at least one review and green CI.
- Contributions are accepted under the repository's licence (inbound = outbound). See `LICENSE`.
- Never commit secrets (`.env`, API keys, tokens, private keys). Never execute untrusted repository code in production.

## How to contribute

1. Find or file an Issue. For a new agent or skill, use the Agent/Skill Submission template.
2. Fork the repo, create a branch, make your change.
3. Run the tests locally: `cd prototype && python3 -m unittest discover -s tests -v` (prototype) — or the repo's own test command once published.
4. Update docs and directory data alongside code. A directory entry without a licence field will not be accepted.
5. Open a PR with a clear description, linked Issue, and test evidence.

## Directory submissions

- One JSON file per entry in `data/directory/`, with all required fields (see `docs/ARCHITECTURE.md` §4).
- Licence is mandatory. Archived/EOL projects are listed with a warning, never recommended.
- Do not submit bulk-generated agents. One working, tested agent at a time.

## Code of Conduct

By participating, you agree to the Code of Conduct in `CODE_OF_CONDUCT.md`.
