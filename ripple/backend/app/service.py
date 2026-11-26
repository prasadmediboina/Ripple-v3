from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import SessionLocal
from .engine import analyze_snapshots
from .engine.graph import build_graph
from .models import (Analysis, AuditLog, CodeNodeRow, DependencyRow, ImpactFindingRow, Organization,
                     PullRequest, Repository, TestRecommendationRow, UsageRecord)
from .sources import get_provider

PLAN_LIMITS = {
    "free":       {"repositories": 1,    "analyses_per_month": 20},
    "pro":        {"repositories": 10,   "analyses_per_month": 500},     # Developer Pro
    "team":       {"repositories": 50,   "analyses_per_month": 5000},
    "enterprise": {"repositories": None, "analyses_per_month": None},
}


# List prices in INR/month. Enterprise is custom-quoted, so it counts as 0 here.
PLAN_PRICES = {"free": 0, "pro": 799, "team": 4999, "enterprise": 0}


class LimitExceeded(Exception):
    pass


def period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def audit(db: Session, org_id: str, user_id: str | None, action: str, detail: str = "") -> None:
    db.add(AuditLog(organization_id=org_id, user_id=user_id, action=action, detail=detail))


def usage_quantity(db: Session, org_id: str, metric: str) -> int:
    row = db.scalar(select(UsageRecord).where(UsageRecord.organization_id == org_id,
                                              UsageRecord.metric == metric, UsageRecord.period == period()))
    return row.quantity if row else 0


def bump_usage(db: Session, org_id: str, metric: str) -> None:
    row = db.scalar(select(UsageRecord).where(UsageRecord.organization_id == org_id,
                                              UsageRecord.metric == metric, UsageRecord.period == period()))
    if row:
        row.quantity += 1
    else:
        db.add(UsageRecord(organization_id=org_id, metric=metric, period=period(), quantity=1))


def check_analysis_quota(db: Session, org: Organization) -> None:
    limit = PLAN_LIMITS[org.plan]["analyses_per_month"]
    if limit is not None and usage_quantity(db, org.id, "analyses") >= limit:
        raise LimitExceeded(f"Monthly analysis limit reached for the {org.plan} plan ({limit}).")


def check_repo_quota(db: Session, org: Organization) -> None:
    limit = PLAN_LIMITS[org.plan]["repositories"]
    if limit is None:
        return
    n = len(db.scalars(select(Repository.id).where(Repository.organization_id == org.id)).all())
    if n >= limit:
        raise LimitExceeded(f"Repository limit reached for the {org.plan} plan ({limit}).")


def index_repository(db: Session, repo: Repository, ref: str) -> dict:
    files = get_provider(repo).snapshot(repo, ref)
    g = build_graph(files)
    db.query(CodeNodeRow).filter_by(repository_id=repo.id).delete()
    db.query(DependencyRow).filter_by(repository_id=repo.id).delete()
    db.add_all(CodeNodeRow(repository_id=repo.id, commit_sha=ref, node_id=n.node_id, name=n.qualname,
                           file_path=n.file_path, node_type=n.node_type, is_test=n.is_test)
               for n in g.nodes.values())
    db.add_all(DependencyRow(repository_id=repo.id, commit_sha=ref, source_id=e.source_id, target_id=e.target_id,
                             relation=e.relation, evidence=e.evidence, resolution=e.resolution) for e in g.edges)
    repo.last_indexed_sha = ref
    audit(db, repo.organization_id, None, "repository.indexed", f"{repo.id}@{ref}")
    db.commit()
    return {"nodes": len(g.nodes), "edges": len(g.edges), "unresolved": len(g.unresolved),
            "parse_errors": g.parse_errors}


def run_analysis(analysis_id: str) -> None:
    """Background job. Opens its own session so it can run in a worker process."""
    with SessionLocal() as db:
        a = db.get(Analysis, analysis_id)
        if not a:
            return
        a.status = "running"
        db.commit()
        try:
            pr = db.get(PullRequest, a.pull_request_id)
            repo = db.get(Repository, pr.repository_id)
            provider = get_provider(repo)
            lookup = (lambda paths: provider.authors(repo, pr.head_sha, paths)) if hasattr(provider, "authors") else None
            report = analyze_snapshots(provider.snapshot(repo, pr.base_sha), provider.snapshot(repo, pr.head_sha), lookup)
            data = report.to_dict()
            a.report, a.status = data, "complete"
            a.completed_at = datetime.now(timezone.utc)
            for f in report.findings:
                db.add(ImpactFindingRow(
                    analysis_id=a.id, changed_node_id=f.changed_node_id, affected_node_id=f.affected_node_id,
                    confidence=f.confidence, depth=f.depth,
                    evidence={"path": [s.__dict__ for s in f.path]},
                    explanation=report.explanations.get(f.affected_node_id, "")))
            for t in report.tests:
                db.add(TestRecommendationRow(analysis_id=a.id, test_node_id=t.test_node_id, reason=t.reason))
            audit(db, a.organization_id, None, "analysis.completed", a.id)
            if settings.post_pr_comments and hasattr(provider, "comment"):
                try:
                    provider.comment(repo, pr.pr_number, report.to_markdown())
                    audit(db, a.organization_id, None, "github.comment_posted", f"pr#{pr.pr_number}")
                except Exception as exc:   # never fail an analysis because the comment could not be posted
                    audit(db, a.organization_id, None, "github.comment_failed", str(exc)[:200])
        except Exception as exc:   # surface a clear failure instead of hanging in "running"
            a.status, a.error = "failed", f"{type(exc).__name__}: {exc}"[:500]
        db.commit()


def enqueue_analysis(analysis_id: str, background_tasks=None) -> None:
    if settings.queue_backend == "celery":
        from .worker import analyze_task
        analyze_task.delay(analysis_id)
    elif background_tasks is not None:
        background_tasks.add_task(run_analysis, analysis_id)
    else:
        run_analysis(analysis_id)


def daily_series(stamps, days: int = 14) -> list[dict]:
    from collections import Counter
    from datetime import timedelta
    today = datetime.now(timezone.utc).date()
    c = Counter(t.date() for t in stamps if t)
    return [{"date": (today - timedelta(d)).isoformat(), "count": c.get(today - timedelta(d), 0)} for d in range(days - 1, -1, -1)]
