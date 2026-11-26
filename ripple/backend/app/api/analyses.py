from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..deps import Ctx, get_ctx, get_db, owned_repo
from ..models import (Analysis, AnalysisFeedback, ImpactFindingRow, PullRequest, Repository,
                      UsageRecord)
from ..service import (PLAN_LIMITS, daily_series, LimitExceeded, audit, bump_usage, check_analysis_quota, enqueue_analysis,
                       period, usage_quantity)

router = APIRouter(tags=["analyses"])


class PRIn(BaseModel):
    repository_id: str
    pr_number: int
    base_sha: str
    head_sha: str
    title: str = ""


class FeedbackIn(BaseModel):
    analysis_id: str
    finding_id: str | None = None
    outcome: str   # confirmed | false_positive | missed_impact
    note: str = ""


def create_analysis(db: Session, org, pr: PullRequest, background_tasks=None, user_id: str | None = None) -> Analysis:
    check_analysis_quota(db, org)
    a = Analysis(organization_id=org.id, pull_request_id=pr.id, status="queued")
    db.add(a)
    bump_usage(db, org.id, "analyses")
    audit(db, org.id, user_id, "analysis.queued", f"pr#{pr.pr_number}")
    db.commit()
    enqueue_analysis(a.id, background_tasks)
    return a


def _owned_pr(db: Session, ctx: Ctx, pr_id: str) -> PullRequest:
    pr = db.scalar(select(PullRequest).join(Repository, Repository.id == PullRequest.repository_id)
                   .where(PullRequest.id == pr_id, Repository.organization_id == ctx.org.id))
    if not pr:
        raise HTTPException(404, "Pull request not found")
    return pr


def _owned_analysis(db: Session, ctx: Ctx, aid: str) -> Analysis:
    a = db.scalar(select(Analysis).where(Analysis.id == aid, Analysis.organization_id == ctx.org.id))
    if not a:
        raise HTTPException(404, "Analysis not found")
    return a


@router.post("/pull-requests", status_code=201)
def register_pr(body: PRIn, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    repo = owned_repo(db, ctx, body.repository_id)
    pr = db.scalar(select(PullRequest).where(PullRequest.repository_id == repo.id, PullRequest.pr_number == body.pr_number))
    if pr:
        pr.base_sha, pr.head_sha, pr.title = body.base_sha, body.head_sha, body.title
    else:
        pr = PullRequest(repository_id=repo.id, pr_number=body.pr_number, base_sha=body.base_sha,
                         head_sha=body.head_sha, title=body.title)
        db.add(pr)
    db.commit()
    return {"id": pr.id, "pr_number": pr.pr_number}


@router.post("/pull-requests/{pr_id}/analyze", status_code=202)
def analyze(pr_id: str, background: BackgroundTasks, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    pr = _owned_pr(db, ctx, pr_id)
    try:
        a = create_analysis(db, ctx.org, pr, background, ctx.user.id)
    except LimitExceeded as e:
        raise HTTPException(402, str(e))
    return {"analysis_id": a.id, "status": a.status}


@router.get("/analyses")
def list_analyses(ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    rows = db.execute(select(Analysis, PullRequest, Repository)
                      .join(PullRequest, PullRequest.id == Analysis.pull_request_id)
                      .join(Repository, Repository.id == PullRequest.repository_id)
                      .where(Analysis.organization_id == ctx.org.id)
                      .order_by(Analysis.created_at.desc()).limit(50)).all()
    return [{"id": a.id, "status": a.status, "created_at": a.created_at, "pr_number": pr.pr_number,
             "title": pr.title, "repository": r.name, "summary": (a.report or {}).get("summary")}
            for a, pr, r in rows]


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    a = _owned_analysis(db, ctx, analysis_id)
    return {"id": a.id, "status": a.status, "error": a.error, "created_at": a.created_at, "report": a.report}


@router.get("/analyses/{analysis_id}/findings")
def findings(analysis_id: str, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    a = _owned_analysis(db, ctx, analysis_id)
    rows = db.scalars(select(ImpactFindingRow).where(ImpactFindingRow.analysis_id == a.id)).all()
    return [{"id": f.id, "changed": f.changed_node_id, "affected": f.affected_node_id, "confidence": f.confidence,
             "depth": f.depth, "evidence": f.evidence, "explanation": f.explanation} for f in rows]


@router.post("/feedback", status_code=201)
def feedback(body: FeedbackIn, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    if body.outcome not in ("confirmed", "false_positive", "missed_impact"):
        raise HTTPException(422, "outcome must be confirmed, false_positive or missed_impact")
    _owned_analysis(db, ctx, body.analysis_id)
    db.add(AnalysisFeedback(analysis_id=body.analysis_id, finding_id=body.finding_id, user_id=ctx.user.id,
                            outcome=body.outcome, note=body.note))
    db.commit()
    return {"recorded": True}


@router.get("/usage")
def usage(ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    limits = PLAN_LIMITS[ctx.org.plan]
    return {"plan": ctx.org.plan, "period": period(), "analyses": usage_quantity(db, ctx.org.id, "analyses"),
            "limits": limits}


@router.get("/dashboard")
def dashboard(ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    """Every number here is computed from stored data. Nothing is estimated or invented."""
    org = ctx.org.id
    repos = db.scalar(select(func.count()).select_from(Repository).where(Repository.organization_id == org))
    done = db.scalars(select(Analysis).where(Analysis.organization_id == org, Analysis.status == "complete")).all()
    ids = [a.id for a in done]
    fb = {}
    if ids:
        for outcome, n in db.execute(select(AnalysisFeedback.outcome, func.count())
                                     .where(AnalysisFeedback.analysis_id.in_(ids)).group_by(AnalysisFeedback.outcome)):
            fb[outcome] = n
    judged = fb.get("confirmed", 0) + fb.get("false_positive", 0)
    return {
        "repositories": repos,
        "analyses_completed": len(done),
        "changed_elements": sum((a.report or {})["summary"]["changed_elements"] for a in done),
        "potentially_affected": sum((a.report or {})["summary"]["potentially_affected"] for a in done),
        "coverage_gaps": sum((a.report or {})["summary"]["coverage_gaps"] for a in done),
        "timeline": daily_series(db.scalars(select(Analysis.created_at).where(Analysis.organization_id == org)).all()),
        "feedback": fb,
        "measured_precision": (fb.get("confirmed", 0) / judged) if judged else None,   # null until real feedback exists
    }
