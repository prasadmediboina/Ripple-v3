"""Founder control room. Only emails listed in ADMIN_EMAILS may call these endpoints."""
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import Ctx, get_ctx, get_db
from ..models import (Analysis, AnalysisFeedback, AuditLog, Lead, Membership, Organization, Repository, Subscription,
                      User)
from ..service import PLAN_LIMITS, PLAN_PRICES, audit, daily_series, period, usage_quantity

router = APIRouter(prefix="/admin", tags=["founder"])
STAGES = ["identified", "contacted", "interviewed", "pilot", "paying", "lost"]
MILESTONES = [1, 5, 20, 50, 100]


def get_admin(ctx: Ctx = Depends(get_ctx)) -> Ctx:
    if ctx.user.email not in settings.admin_emails:
        raise HTTPException(403, "Founder access only")
    return ctx


@router.get("/overview")
def overview(ctx: Ctx = Depends(get_admin), db: Session = Depends(get_db)):
    orgs = db.scalars(select(Organization)).all()
    subs = db.scalars(select(Subscription).where(Subscription.status.in_(["active", "cancelling", "past_due"]),
                                                  Subscription.plan != "free")).all()
    billed_ids = {x.organization_id for x in subs}
    paying = len(billed_ids)
    comped = sum(1 for o in orgs if o.plan != "free" and o.id not in billed_ids)
    fb = dict(db.execute(select(AnalysisFeedback.outcome, func.count()).group_by(AnalysisFeedback.outcome)).all())
    judged = fb.get("confirmed", 0) + fb.get("false_positive", 0)
    analyses = db.scalars(select(Analysis.created_at)).all()
    return {
        "users": db.scalar(select(func.count()).select_from(User)),
        "organizations": len(orgs),
        "repositories": db.scalar(select(func.count()).select_from(Repository)),
        "analyses_total": len(analyses),
        "plans": dict(Counter(o.plan for o in orgs)),
        "paying_teams": paying,
        "comped_teams": comped,
        "mrr_inr": sum(PLAN_PRICES[x.plan] for x in subs),
        "list_price_mrr_inr": sum(PLAN_PRICES[o.plan] for o in orgs),
        "mrr_note": "Billed MRR counts teams with an active paid subscription, at list price. Comped/pilot plans set by hand are excluded.",
        "milestones": [{"target": m, "reached": paying >= m} for m in MILESTONES],
        "signups": daily_series(db.scalars(select(User.created_at)).all()),
        "analyses_daily": daily_series(analyses),
        "feedback": fb,
        "measured_precision": (fb.get("confirmed", 0) / judged) if judged else None,
        "leads": dict(Counter(l for (l,) in db.execute(select(Lead.stage)).all())),
    }


@router.get("/organizations")
def organizations(ctx: Ctx = Depends(get_admin), db: Session = Depends(get_db)):
    out = []
    for o in db.scalars(select(Organization)).all():
        out.append({"id": o.id, "name": o.name, "plan": o.plan,
                    "members": db.scalar(select(func.count()).select_from(Membership).where(Membership.organization_id == o.id)),
                    "repositories": db.scalar(select(func.count()).select_from(Repository).where(Repository.organization_id == o.id)),
                    "analyses_this_month": usage_quantity(db, o.id, "analyses"), "period": period()})
    return out


class PlanIn(BaseModel):
    plan: str


@router.patch("/organizations/{org_id}/plan")
def set_plan(org_id: str, body: PlanIn, ctx: Ctx = Depends(get_admin), db: Session = Depends(get_db)):
    if body.plan not in PLAN_LIMITS:
        raise HTTPException(422, f"plan must be one of {list(PLAN_LIMITS)}")
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(404, "Organization not found")
    old, org.plan = org.plan, body.plan
    # Deliberately does NOT touch Subscription: a hand-set plan grants access (comp/pilot) but is not revenue.
    audit(db, org.id, ctx.user.id, "admin.plan_changed", f"{old} -> {body.plan}")
    db.commit()
    return {"id": org.id, "plan": org.plan}


@router.get("/audit")
def audit_log(limit: int = 40, ctx: Ctx = Depends(get_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 200))).all()
    return [{"id": r.id, "organization_id": r.organization_id, "action": r.action, "detail": r.detail, "created_at": r.created_at} for r in rows]


class LeadIn(BaseModel):
    name: str
    company: str = ""
    contact: str = ""
    stage: str = "identified"
    note: str = ""


class LeadPatch(BaseModel):
    stage: str | None = None
    note: str | None = None


def _lead(l: Lead) -> dict:
    return {"id": l.id, "name": l.name, "company": l.company, "contact": l.contact, "stage": l.stage, "note": l.note}


@router.get("/leads")
def leads(ctx: Ctx = Depends(get_admin), db: Session = Depends(get_db)):
    return {"stages": STAGES, "leads": [_lead(l) for l in db.scalars(select(Lead).order_by(Lead.created_at)).all()]}


@router.post("/leads", status_code=201)
def add_lead(body: LeadIn, ctx: Ctx = Depends(get_admin), db: Session = Depends(get_db)):
    if body.stage not in STAGES:
        raise HTTPException(422, f"stage must be one of {STAGES}")
    l = Lead(**body.model_dump())
    db.add(l)
    db.commit()
    return _lead(l)


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: str, body: LeadPatch, ctx: Ctx = Depends(get_admin), db: Session = Depends(get_db)):
    l = db.get(Lead, lead_id)
    if not l:
        raise HTTPException(404, "Lead not found")
    if body.stage is not None:
        if body.stage not in STAGES:
            raise HTTPException(422, f"stage must be one of {STAGES}")
        l.stage = body.stage
    if body.note is not None:
        l.note = body.note
    l.updated_at = datetime.now(timezone.utc)
    db.commit()
    return _lead(l)


@router.delete("/leads/{lead_id}", status_code=204)
def delete_lead(lead_id: str, ctx: Ctx = Depends(get_admin), db: Session = Depends(get_db)):
    l = db.get(Lead, lead_id)
    if l:
        db.delete(l)
        db.commit()
