# Roadmap and validation plan

## Phase 0: prove the engine (weeks 1–4)
- Build 20+ verified change cases from real open-source Python repos in `benchmarks/`; publish precision/recall.
- Dogfood the CLI on Ripple itself and 2–3 friendly projects.

## Phase 1: design partners (weeks 4–10)
- Register a GitHub App, test `GitHubProvider` end-to-end, wire the install flow into the dashboard.
- Recruit 5 startup teams (5–50 devs). Success = they open reports on ≥50% of PRs and mark findings.
- Interview questions: how do you check impact today, what did the last bad merge cost, would you pay ₹799/₹4,999?

## Phase 2: revenue (months 3–6)
- Billing (Razorpay for INR / Stripe for USD) writing to `subscriptions`; plan enforcement already exists.
- TypeScript/JavaScript and Java via tree-sitter. Runtime coverage import (coverage.py, JaCoCo).

## Phase 3: moat (months 6–12)
- Service-to-service and API-contract edges (OpenAPI, gRPC). Historical co-change mining.
- Per-repo learned risk from feedback. Private deployment for fintech.

## Targets from the blueprint
First paying customer → 5 → 20 → 50 → 100 teams. Treat pricing as a hypothesis until teams pay.
Revenue figures in the blueprint are illustrative, not forecasts.

## Naming check (do this first)
A public developer tool also called "Ripple" exists (AI-assisted PR impact analysis). Before investing in branding, check
trademarks, domains and GitHub org names, and consider a distinctive variant. This is a product-name risk, not a code issue.

## Ideas from competitor research, with honest scoping
- Reviewer suggestions: built (git history, CLI/local); GitHub API history lookup next.
- Risk score: built as a transparent heuristic. "AI bug prediction" is NOT claimed; calibrate the score against feedback first.
- Engineering analytics (recurring risky modules, trends): next, once real analyses accumulate.
