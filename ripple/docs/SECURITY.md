# Security model

| Control | Implementation |
|---|---|
| Read-only source access | GitHub App with `contents: read`; short-lived installation tokens, never stored |
| Code is never executed | Analysis reads git objects/zip archives only; zip-bomb limits (size, file count) in `sources.py` |
| Webhook authenticity | HMAC-SHA256 `X-Hub-Signature-256`, constant-time compare (`security.py`) |
| Secrets at rest | Fernet encryption for stored credentials; `ENCRYPTION_KEY` mandatory in production |
| Passwords | scrypt with per-user salt; JWT sessions (12h) |
| Tenant isolation | Every query is scoped to the caller's organization (`deps.owned_repo`, org-filtered analyses); covered by tests |
| Audit trail | `audit_logs` records indexing, analyses, integrations |
| LLM privacy | Off by default; requires `Organization.llm_consent`; only names/paths/evidence strings, never file bodies |
| Local repos | `ALLOW_LOCAL_REPOS` is dev/self-hosted only and refuses to start in production |
| Self-hosted option | CLI/GitHub Action runs in the customer's CI; nothing is uploaded |

## Known gaps before enterprise sales
Rate limiting, refresh tokens/session revocation, RBAC beyond `owner`, SSO/SAML, SOC 2 evidence collection,
per-analysis resource sandboxing for future test execution (containers with CPU/memory/time limits),
dependency/secret scanning of this repo in CI. The frontend stores the JWT in `localStorage`; move to
HttpOnly cookies before handling sensitive customers.
