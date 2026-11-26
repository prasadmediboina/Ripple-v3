import hashlib
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import billing_provider
from ..config import settings
from ..deps import Ctx, get_ctx, get_db
from ..models import BillingEvent, Organization, Subscription
from ..security import verify_razorpay_signature
from ..service import PLAN_LIMITS, PLAN_PRICES, audit

router = APIRouter(tags=["billing"])
PLANS = {"pro": ("Developer Pro", "razorpay_plan_pro"), "team": ("Team", "razorpay_plan_team")}
ACTIVE = {"subscription.activated", "subscription.charged", "subscription.resumed"}
ENDED = {"subscription.cancelled", "subscription.completed", "subscription.halted", "subscription.expired"}


def configured() -> bool:
    return all([settings.razorpay_key_id, settings.razorpay_key_secret, settings.razorpay_webhook_secret,
                settings.razorpay_plan_pro, settings.razorpay_plan_team])


def _sub(db: Session, org_id: str) -> Subscription:
    sub = db.scalar(select(Subscription).where(Subscription.organization_id == org_id))
    if not sub:
        sub = Subscription(organization_id=org_id, plan="free", status="active")
        db.add(sub)
    return sub


class CheckoutIn(BaseModel):
    plan: str


@router.get("/billing")
def billing(ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    sub = _sub(db, ctx.org.id)
    return {"configured": configured(), "plan": ctx.org.plan, "can_manage": ctx.role == "owner",
            "subscription": {"plan": sub.plan, "status": sub.status},
            "plans": [{"id": k, "name": v[0], "price_inr": PLAN_PRICES[k], "limits": PLAN_LIMITS[k]} for k, v in PLANS.items()]}


@router.post("/billing/checkout")
def checkout(body: CheckoutIn, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    if ctx.role != "owner":
        raise HTTPException(403, "Only the team owner can change the subscription")
    if body.plan not in PLANS:
        raise HTTPException(422, "plan must be 'pro' or 'team'. Contact us for Enterprise.")
    if not configured():
        raise HTTPException(503, "Payments are not configured on this deployment yet.")
    sub = _sub(db, ctx.org.id)
    if sub.plan != "free" and sub.status in ("active", "cancelling", "past_due"):
        raise HTTPException(409, "Cancel your current subscription before choosing another plan.")
    try:
        created = billing_provider.get_client().create_subscription(getattr(settings, PLANS[body.plan][1]), ctx.org.id, ctx.user.email)
    except Exception:
        raise HTTPException(502, "The payment provider returned an error. Please try again.")
    sub.plan, sub.status, sub.external_id = body.plan, "created", created["id"]
    audit(db, ctx.org.id, ctx.user.id, "billing.checkout_started", f"{body.plan} {created['id']}")
    db.commit()
    return {"checkout_url": created["short_url"], "subscription_id": created["id"]}


@router.post("/billing/cancel")
def cancel(ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    if ctx.role != "owner":
        raise HTTPException(403, "Only the team owner can change the subscription")
    sub = _sub(db, ctx.org.id)
    if not sub.external_id or sub.status not in ("active", "past_due"):
        raise HTTPException(409, "There is no active subscription to cancel.")
    try:
        billing_provider.get_client().cancel_subscription(sub.external_id, at_cycle_end=True)
    except Exception:
        raise HTTPException(502, "The payment provider returned an error. Please try again.")
    sub.status = "cancelling"          # access continues; the provider's webhook ends it
    audit(db, ctx.org.id, ctx.user.id, "billing.cancel_requested", sub.external_id)
    db.commit()
    return {"status": sub.status}


@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db),
                           x_razorpay_signature: str | None = Header(default=None),
                           x_razorpay_event_id: str | None = Header(default=None)):
    body = await request.body()
    if not verify_razorpay_signature(body, x_razorpay_signature, settings.razorpay_webhook_secret):
        raise HTTPException(401, "Invalid webhook signature")
    event_id = x_razorpay_event_id or hashlib.sha256(body).hexdigest()
    if db.get(BillingEvent, event_id):
        return {"duplicate": True}
    data = json.loads(body)
    event = data.get("event", "")
    ent = (((data.get("payload") or {}).get("subscription") or {}).get("entity")) or {}
    sub = db.scalar(select(Subscription).where(Subscription.external_id == ent["id"])) if ent.get("id") else None
    if sub:
        org = db.get(Organization, sub.organization_id)
        if event in ACTIVE:
            sub.status, org.plan = "active", sub.plan
            audit(db, org.id, None, "billing.active", f"{sub.plan} via {event}")
        elif event in ENDED:
            sub.status, org.plan = event.split(".")[1], "free"
            audit(db, org.id, None, "billing.ended", event)
        elif event == "subscription.pending":
            sub.status = "past_due"
            audit(db, org.id, None, "billing.payment_pending", sub.external_id or "")
    db.add(BillingEvent(id=event_id, event=event[:60]))
    db.commit()
    return {"ok": True}
