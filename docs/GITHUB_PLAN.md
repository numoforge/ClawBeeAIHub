> **Decision 2026-11-20:** Brand is ClawBee. Repo is `numoforge/ClawBeeAIHub` (personal account, no Organization). Licence Apache-2.0, public, GitHub Free ($0).

# ClawBee — GitHub Implementation Plan

**Status:** Plan v0.1, 2026-11-20. Local only, nothing published.
**GitHub account (verified):** `numoforge` (putra238a@gmail.com), login confirmed 2026-11-20 19:25 WIB, no 2FA on that sign-in.
**Constraint:** GitHub ONLY. No website, VPS, paid hosting, or custom domain.

## 1. Approval gates (each needs Jeniffer's explicit approval, separately)

| # | Gate | Status |
|---|---|---|
| 1 | Org slug: `clawbee` (fallbacks `clawbee-ai`, `clawbee-hub`, `clawbee-agents`) — confirm availability + exact slug | NOT approved |
| 2 | Org owners: Owner #1 = numoforge; Owner #2 (if any) + 2FA on both | NOT approved |
| 3 | Billing: GitHub Free ($0), no paid plan, no payment method | NOT approved |
| 4 | Licence: Apache-2.0 (recommended) vs MIT; copyright holder name | NOT approved |
| 5 | First repos: `.github` + `clawbee` only | NOT approved |
| 6 | Publish gate for `clawbee`: README, LICENSE, CONTRIBUTING, SECURITY, CI green, tests pass, no secrets — owner reviews contents locally before first push | NOT approved |
| 7 | Branch protection / rulesets on `main` (PR + ≥1 review + CI) | NOT approved |
| 8 | Security settings: private vulnerability reporting, Dependabot, secret scanning + push protection, CodeQL | NOT approved |
| 9 | Community: Discussions on? Categories? Code of Conduct adopted? | NOT approved |

No org creation, repo creation, push, Pages publish, release, or announcement until its gate is approved.

## 2. Publish order

1. **`.github`** (first, with the org) — profile README (`profile/README.md`), org-wide CONTRIBUTING / CODE_OF_CONDUCT / SECURITY, issue + PR templates, reusable Actions workflows. Templates for this are prepared locally in `templates/`.
2. **`clawbee`** (core monorepo) — only when the v0.1 prototype is tested locally, README + LICENSE + CI are ready, and the owner has reviewed the contents locally.
3. Splits (`clawbee-directory`, `clawbee-factory`, `clawbee-orchestrator`, `clawbee-agents`) — only on evidence (different versioning, licence, access, or independent usability), one working tested component at a time.

## 3. Repo layout (monorepo `clawbee`, Phase 1)

```
clawbee/
  README.md  LICENSE  CONTRIBUTING.md  CODE_OF_CONDUCT.md  SECURITY.md  AGENTS.md
  packages/core/  packages/directory/  packages/factory/
  packages/orchestration/  packages/providers/  packages/skills/
  apps/cli/
  data/directory/  data/skills/
  docs/
  .github/workflows/ci.yml  .github/dependabot.yml  .github/CODEOWNERS
  .github/ISSUE_TEMPLATE/  .github/pull_request_template.md
```

Naming: lowercase hyphenated, category prefixes (`core-*`, `*-sdk` for future splits).

## 4. Teams (proposal, create only after org approval)

- `@clawbee/owners` — Jeniffer + Owner #2; Admin on all repos
- `@clawbee/core` — Write/Maintain on `clawbee`
- `@clawbee/docs` — Write on `docs/` (CODEOWNERS)
- `@clawbee/security` — CODEOWNERS for `/.github/`, workflows, SECURITY.md
- `@clawbee/community` — Triage, only when there is a community to moderate

Base permission: Read. Access via teams, never individuals. ≥2 owners, 2FA required.

## 5. Issues / Projects / Discussions

- Labels (~12): `bug`, `enhancement`, `feature`, `documentation`, `refactor`, `question`, `priority:critical/high/medium/low`, `status:needs-triage/blocked/help-wanted`, `effort:small/medium/large`, plus `good first issue`, `help wanted`.
- Issue templates: Bug Report, Feature Request, Agent/Skill Submission, Documentation (required fields).
- One org Project: "ClawBee Roadmap" (Roadmap view + Sprint Backlog). Milestones: `v0.1 core + directory`, `v0.2 factory`, `v0.3 orchestration`.
- Discussions categories: Announcements (maintainers only), Q&A, Ideas, Show and Tell, General.
- Rule: every piece of work is an Issue before it is a PR; every PR links its Issue.

## 6. CI / CD / security (Actions)

- `ci.yml` (prepared in `templates/.github/workflows/`): runs on push to `main` + PRs — lint/format, unit tests (stdlib `unittest`), build check. Named checks, required in branch protection.
- Pin third-party actions to full 40-char SHA (Dependabot `github-actions` ecosystem updates them).
- `permissions: contents: read` at workflow top; least privilege per job. Never `pull_request_target` with untrusted checkout. Never interpolate user input into `run:`.
- Dependabot: weekly, `open-pull-requests-limit: 10`, groups, cooldown (3d minor/patch, 14d major).
- CodeQL Default setup: push + PR + weekly. Secret scanning + push protection on. Gitleaks as second layer in CI.
- Licence check in CI: fail on a dependency licence outside the allow-list (MIT, Apache-2.0, BSD, CC0/CC-BY for data).
- SBOM (SPDX) on every release; signed tags for releases; `actions/attest-build-provenance` for published artifacts.
- Scheduled discovery (weekly, Phase v0.4): read-only GitHub Search API → data-file update → PR. Never auto-merge, never push to `main`, never clone/run untrusted code in that job. 6-hour job limit.

## 7. Local templates prepared (in `templates/`)

- `LICENSE` — full Apache-2.0 text (fetched from apache.org, 2026-11-20). Copyright line to confirm with owner before publish.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant), `SECURITY.md` (see §6), `README.md` (monorepo draft), `AGENTS.md`.
- `.github/workflows/ci.yml`, `.github/dependabot.yml`, `.github/CODEOWNERS`, issue/PR templates.

## 8. What will NOT be done

- No empty repos, no "coming soon" publishes, no bulk-published untested generated agents.
- No secrets in code/issues/logs. No auto-merged bot PRs. No promised Free-plan features that are paid (SAML/SSO, Advanced Security on private repos).
- No website/VPS/domain/crypto repos.

## 9. Cost

GitHub Free $0 for the whole public phase. Local dev $0. Total Phase 1: **$0**.
