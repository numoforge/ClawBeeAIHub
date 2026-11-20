# ClawBee — Architecture

**Status:** Design v0.1, 2026-11-20. Local only, not published.
**Sources:** `research/frameworks.md`, `research/mcp-models.md`, `research/github-org.md` (all checked 2026-11-20).
**Constraints:** GitHub-only distribution. No website, VPS, paid hosting, or custom domain. No hard dependency on a single proprietary LLM provider. Never execute untrusted repo code in production.

## 1. Decisions (with reasons)

| Decision | Choice | Why | Alternative / fallback |
|---|---|---|---|
| Orchestration core | LangGraph library only (MIT), Python | Durable checkpoints, `interrupt()` HITL, sequential/parallel via Send fan-out, hierarchical via subgraphs — matches all hard requirements (§6 frameworks.md) | Google ADK (Apache-2.0) — like-for-like replacement |
| Orchestration NOT used | LangGraph Agent Server / LangSmith | Agent Server is Elastic-2.0, needs LangSmith licence key for self-hosting; would break the MIT-only public-platform story | Self-host library + Postgres checkpointer |
| Skill format | Agent Skills open standard (`SKILL.md` + frontmatter) | Portable across hosts, progressive disclosure, spec at agentskills.io | — |
| Tool protocol | MCP spec 2026-07-28 | Stateless core, Skills extension SEP-2640, formal deprecation policy | Direct tool calls only inside sandboxed, allow-listed adapters |
| Model gateway | LiteLLM Proxy (MIT core) as the only gateway | 100+ providers, virtual keys, budgets, fallback chains; OpenAI-compatible Chat Completions as narrow waist | Direct provider clients per adapter (no gateway) — loses budgets/fallbacks |
| Model backends | Ollama (dev) → vLLM/SGLang (prod GPU) → llama.cpp (CPU/edge) → OpenRouter / HF Inference Providers (hosted open-weight) | No proprietary hard dependency; fail closed, never silently swap model/licence | — |
| Observability / eval | Phoenix (Apache-2.0) for tracing; Langfuse (MIT) for eval flywheel; Inspect AI (MIT) for benchmarks | Self-hostable, no mandatory SaaS; `pass^k` reliability metric | LangSmith only if already on LangChain — never mandatory |
| Repo layout | One public monorepo `clawbee` first; split only on evidence | Avoids empty-repo failure; LangChain hybrid pattern (monorepo + split integrations) | Multi-repo from day one — rejected |
| Licence (code) | Apache-2.0 (recommended, owner to confirm) | Permissive + explicit patent grant; corporate-friendly | MIT fallback |
| Licence (docs/data) | CC-BY-4.0 docs, CC0 directory factual data | Avoids doubt on reuse | — |

**Excluded, with reason:** AutoGen (archived, no security fixes), Flowise (archived/EOL 2026-08-31), Dify as hosted multi-tenant service (modified Apache-2.0 bars it), n8n as hosted public service (Sustainable Use License bars it). All four remain directory entries with warnings.

## 2. System overview

```
                         ┌─────────────────────────────┐
                         │  GitHub (home/distribution) │
                         │  org `clawbee` (proposed)   │
                         │  .github │ clawbee (monorepo)│
                         └──────────────┬──────────────┘
                                        │ PR + review + CI
                         ┌──────────────▼──────────────┐
                         │  ClawBee core (this repo)   │
                         │  directory · factory ·      │
                         │  orchestration · providers  │
                         └──────┬──────────┬───────────┘
                    ┌───────────▼───┐  ┌───▼────────────┐
                    │ LiteLLM Proxy │  │ MCP servers    │
                    │ (MIT core)    │  │ (allow-listed, │
                    │ model gateway │  │ sandboxed)     │
                    └──────┬────────┘  └────────────────┘
                           │ OpenAI-compatible
              ┌────────────┼────────────┬──────────────┐
              ▼            ▼            ▼              ▼
           Ollama      vLLM/SGLang  llama.cpp    OpenRouter/HF
           (dev)       (prod GPU)   (CPU/edge)   (hosted open-weight)
```

No component calls a proprietary provider directly. Every model call goes through the provider adapter → LiteLLM Proxy config. The prototype in `prototype/` implements the adapter interface with a stub (no network, no keys) so the design is testable without any provider account.

## 3. Modules (monorepo `clawbee`, Phase 1)

```
clawbee/
  packages/
    core/            # schemas, validation, audit log, state store
    directory/       # directory data (JSON) + loader + search + vetting fields
    factory/         # agent/skill generation from templates + version history
    orchestration/   # sequential / parallel / hierarchical runs, HITL, recovery
    providers/       # model-agnostic adapter interface + LiteLLM config
    skills/          # SKILL.md parsing + validation (Agent Skills standard)
  apps/
    cli/             # `clawbee` CLI: directory search, factory generate, run
  data/
    directory/       # one JSON file per entry; licence + maintenance + security fields
    skills/          # one folder per skill, SKILL.md + scripts/ + references/
  docs/              # architecture, GitHub plan, contributing, security
  .github/           # workflows, CODEOWNERS, dependabot, issue/PR templates
```

Prototype maps 1:1 to this layout, in miniature, under `prototype/` (stdlib-only Python, no external deps).

## 4. Data model — directory entry (v0.1)

One JSON file per entry. Required fields: `id`, `name`, `description`, `repo` (owner/repo + URL), `license`, `license_osi` (true/false + note), `status` (`active` | `archived` | `eol`), `framework` / `category`, `languages`, `features[]`, `install` (commands or "see repo"), `maintenance` (`last_release`, `last_release_date`, `stars_as_of`, `checked_date`), `security` (`assessment`, `known_cves` / `notes`, `sandbox_required` bool), `compatibility` (`models`, `mcp` bool, `a2a` bool), `sources[]` (URLs + checked date).

Rules: no entry without a `license` field — "unknown" is a finding, not a gap to guess. Archived/EOL entries are listed with a warning, never recommended. Licence traps (Dify, n8n) are flagged in `license_osi: false` + note.

## 5. Data model — generated agent (v0.1)

```
agent/
  agent.json         # id, name, version, purpose, framework, model (adapter ref, not a vendor name),
                     # tools (MCP server allow-list), skills[], human_approval (list of sensitive actions),
                     # eval (task suite refs), created_from (template + version)
  SKILL.md files     # one per skill, Agent Skills format
  tests/             # scripted task suite: task, expected, pass/fail
  HISTORY.md         # version history: version, date, change, author
```

Generated agents are reproducible: same template + same inputs → same `agent.json` (deterministic, no timestamps inside the generated config except a separate `generated_at` in HISTORY). No secrets in generated files, ever.

## 6. Orchestration semantics (v0.1, prototype implements this)

- **Sequential:** steps run in order; each step's output feeds the next; any step failure stops the run unless its `on_error` is `continue` (logged) or `retry` (max 3, backoff).
- **Parallel:** steps fan out, results collected in order; one failure does not cancel siblings; run fails if any required step fails.
- **Hierarchical:** a step may be a sub-run (subgraph); parent state is checkpointed before delegating; child failure propagates as a step failure with its audit trail attached.
- **Human-in-the-loop:** a step with `requires_approval: true` pauses the run, checkpoints state to disk, and waits for an explicit approve/reject/edit decision. No timeout in the framework — ClawBee sets a default 24h timeout with escalation to the owner, recorded in the audit log. Unanswered approval never auto-approves.
- **Persistent state:** JSON checkpoint per run (`state/<run_id>.json`): run id, step index, step results, status. Resume replays from the checkpoint, never re-runs completed steps.
- **Error recovery:** retry (bounded), skip-if-optional, abort-with-partial-results. Every transition is audit-logged (who/what/when, append-only JSONL).
- **Agent-to-agent:** agents communicate only through the orchestrator (structured messages in state), never by direct network calls. A2A adapter is a v2 design item, not a v1 dependency.

## 7. Security model

- Sandbox execution: untrusted agent code never runs in production; prototype runs steps as pure Python callables in-process only for local testing — production runs go through Docker+gVisor (trusted) or Firecracker/E2B (untrusted), default-deny egress, per-run credentials.
- Dependency scanning: Dependabot + CodeQL Default setup + secret scanning/push protection on every repo; SBOM (SPDX) on every release; pinned Action SHAs.
- Prompt injection: MCP tool descriptions are untrusted input — snapshot + diff on update, re-approve on change; never combine private data + untrusted input + exfiltration in one agent without approval for the exfiltration step ("lethal trifecta").
- Secrets: env vars / secret manager only; never in code, issues, PRs, logs, or example configs. `GITHUB_TOKEN` least-privilege (`contents: read` default).
- Access: org base permission Read, access via teams, ≥2 owners, 2FA required; branch protection/rulesets on `main` (PR + ≥1 review + CI, no force-push/delete).
- Audit: append-only JSONL audit log per run; org audit log reviewed on org changes.

## 8. Discovery & maintenance (autonomous, but gated)

- Scheduled GitHub Action (weekly): read-only GitHub Search API for new agent repos → update `data/directory/` candidates → open a PR. Never auto-merge, never push to `main`, never clone/run untrusted code in the discovery job.
- Dependency monitoring: Dependabot weekly PRs, CodeQL weekly, licence check in CI (allow-list).
- Health checks: directory entries re-checked (maintenance + security fields) on a schedule; stale entries flagged, archived entries downgraded.
- No uncontrolled production self-modification: every change is a PR + human review + CI green.

## 9. Owner dashboard (private, Phase 2)

Private dashboard (GitHub Projects + a local/CLI summary first; no separate hosted dashboard in Phase 1): total discovered agents, active agents, execution status, new repos/skills discovered, research reports, system health, failed jobs, resource consumption, API usage, security alerts, pending approvals. Phase 1 delivers this as `clawbee status` CLI output + the org Project board, not a hosted web app.

## 10. Roadmap

- **v0.1 (now, local):** research + architecture + working prototype (directory, factory, orchestration, providers stub) + tests green + templates. No publishing.
- **v0.2 (after owner approval):** create org `clawbee` + `.github` repo + `clawbee` monorepo; publish prototype as v0.1 with README/LICENSE/CONTRIBUTING/SECURITY/CI.
- **v0.3:** factory + eval harness (Phoenix/Langfuse + Inspect AI task suites, `pass^k`), first curated agent (tested, one at a time).
- **v0.4:** scheduled discovery Action, directory API/CLI search, owner dashboard (CLI + Project board).
- **v1.0:** public marketplace (discover/browse/test/share via GitHub), community contributions with quotas + abuse protection, A2A adapter design.

## 11. Infrastructure & cost estimate (verified, 2026-11-20)

- GitHub Free ($0): unlimited public repos, unlimited public-repo Actions minutes on standard runners, Dependabot alerts, Pages. No paid plan needed for the public phase.
- Local dev: $0 (stdlib-only prototype; Ollama local models optional, user hardware).
- LiteLLM Proxy / vLLM / Ollama: open-source, self-hosted — $0 licence cost; GPU hosting is the only real cost if/when ClawBee self-hosts inference, and it is out of scope for Phase 1 (prototype uses a stub, no inference).
- Total Phase 1 cost: **$0**. No purchase, no payment method, no paid service is required or authorised.
