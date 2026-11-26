# Ripple

**Understand every change. Predict every impact.**

Ripple analyzes a pull request, traces what the change can reach through your code, and reports
the exact dependency path behind every warning, the tests worth running, and the code no test reaches.
Findings are *potential impacts*, never "defects": a dependency is not a failure.

## What's in this repository

| Path | What it is |
|---|---|
| `backend/app/engine` | Deterministic analysis engine: parser → dependency graph → diff → impact traversal → test selection |
| `backend/app/api` | FastAPI service: auth, organizations, repositories, PR analysis, webhooks, feedback, usage, dashboard |
| `backend/app/cli.py` | CLI that runs fully inside your own CI (source never leaves your infrastructure) |
| `frontend` | Next.js app: landing page, auth, dashboard, interactive impact-graph report, sample workspace |
| `integrations/github-action` | Drop-in workflow that posts the report as a PR comment |
| `backend/app/engine/risk.py` | Explainable PR risk score (every point traced to a named factor) |
| `benchmarks` | Precision/recall harness for human-verified change cases |
| `docs` | Architecture, security model, roadmap and validation plan |

## Founder control room

Sign in with an email listed in `ADMIN_EMAILS` (e.g. `ADMIN_EMAILS=you@example.com`) to open **Command center**:
users, paying teams, list-price MRR, milestone tracker (1 / 5 / 20 / 50 / 100 teams), signup and analysis charts,
a customer-discovery pipeline (identified → contacted → interviewed → pilot → paying), per-team plan control and an
activity feed. MRR is a list-price estimate until billing is connected. The sample workspace shows it with fictional data.

## Payments, GitHub and deployment

- **Payments:** Razorpay subscriptions in INR, webhook-verified, idempotent. See `docs/BILLING.md`.
- **GitHub App:** install flow, repository import, automatic PR comments. See `docs/GITHUB_APP.md`.
- **Deploy:** `render.yaml` blueprint. See `docs/DEPLOY_RENDER.md`. Checklist: `docs/LAUNCH_CHECKLIST.md`.
- **Legal:** starter `/terms` and `/privacy` pages (templates, need lawyer review).

## Quick start

```bash
# 1. Backend
cd backend && pip install -r requirements-dev.txt
python -m pytest -q                      # 25 tests: engine, API, billing, founder tools
ALLOW_LOCAL_REPOS=true uvicorn app.main:app --reload     # http://localhost:8000/docs

# 2. Frontend
cd frontend && npm install && npm run dev                 # http://localhost:3000
# Click "Explore a sample workspace" for a fully populated demo (clearly labelled fictional data)

# 3. Try the engine on any git repo, no server needed
cd backend && python -m app.cli analyze --repo /path/to/repo --base main --head HEAD

# 4. Everything together (Postgres, Redis, API, Celery worker, web)
cp .env.example .env && docker compose up --build
```

## Honest status

Working and tested: Python analysis (functions, methods, classes, imports incl. relative, inheritance,
`self.` calls), AST-based change detection (formatting/comment edits are ignored), evidence-backed
impact paths with confidence, static test selection and coverage gaps, explicit "unknowns", multi-tenant
API with plan limits, encrypted secrets, signed webhooks, audit log, feedback-driven precision.

Tested with mocks only (no live accounts): Razorpay billing and the GitHub App provider/flow (`app/sources.py`, `app/api/github.py`),
plus the Celery path. Run them in Razorpay Test Mode and on a throwaway repository before real customers. Test them with a real GitHub App before onboarding customers (see `docs/ROADMAP.md`).

Not built yet: languages other than Python (tree-sitter adapters), runtime coverage, GitHub commit-history reviewers,
service/API-contract dependencies, email notifications, SSO.

## Before you claim accuracy

`benchmarks/` ships one self-authored case, so a perfect score only proves the harness works.
Add real open-source change cases with human-verified expected impacts, then publish those numbers.
