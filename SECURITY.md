# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes (prototype) |

## Reporting a vulnerability

**Do not report vulnerabilities in a public issue.**

Use GitHub's private vulnerability reporting on the repository
(Security → Report a vulnerability). Only maintainers can see the report.

We aim to acknowledge within 48 hours, assess within 7 days, and fix or
mitigate high-severity issues within 30 days. These are targets, not
guarantees. Reporters will be credited unless they ask not to be.

## Scope notes

- ClawBee lists agent code; it does not run untrusted directory code in production.
- MCP servers in the directory are allow-listed and sandboxed; a listing is discovery, not a safety verdict.
- If a secret is ever committed, revoke/rotate it first, then clean history.
