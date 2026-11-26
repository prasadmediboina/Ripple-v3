import hashlib, hmac, json
import jwt
import pytest
from fastapi.testclient import TestClient

from app import billing_provider, config, db as dbmod


class FakeRazorpay:
    def __init__(self): self.cancelled = []
    def create_subscription(self, plan_id, org_id, email, total_count=120): return {"id": "sub_123", "short_url": "https://rzp.io/i/abc"}
    def cancel_subscription(self, sid, at_cycle_end=True): self.cancelled.append(sid)


@pytest.fixture
def env(monkeypatch):
    s = config.settings
    for k, v in dict(razorpay_key_id="k", razorpay_key_secret="s", razorpay_webhook_secret="whsec", razorpay_plan_pro="plan_pro",
                     razorpay_plan_team="plan_team", github_app_slug="ripple-test", admin_emails=["boss@x.io"]).items():
        monkeypatch.setattr(s, k, v)
    fake = FakeRazorpay()
    monkeypatch.setattr(billing_provider, "get_client", lambda: fake)
    eng = dbmod.make_engine("sqlite:///:memory:")
    dbmod.SessionLocal.configure(bind=eng)
    from app.models import Base
    Base.metadata.create_all(eng)
    from app.main import app
    return TestClient(app), fake


def hdr(c, email="dev@x.io"):
    t = c.post("/api/v1/auth/register", json={"email": email, "password": "correct-horse-1"}).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


def hook(c, event, sub_id="sub_123", event_id="evt_1", secret="whsec"):
    body = json.dumps({"event": event, "payload": {"subscription": {"entity": {"id": sub_id}}}}).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return c.post("/api/v1/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": sig, "X-Razorpay-Event-Id": event_id})


def test_full_payment_lifecycle(env):
    c, fake = env
    h = hdr(c)
    assert c.get("/api/v1/billing", headers=h).json()["plan"] == "free"
    r = c.post("/api/v1/billing/checkout", headers=h, json={"plan": "pro"}).json()
    assert r["checkout_url"] == "https://rzp.io/i/abc"
    assert c.get("/api/v1/billing", headers=h).json()["plan"] == "free"          # not upgraded until payment is confirmed
    assert hook(c, "subscription.activated").status_code == 200
    b = c.get("/api/v1/billing", headers=h).json()
    assert b["plan"] == "pro" and b["subscription"]["status"] == "active"
    assert c.get("/api/v1/usage", headers=h).json()["limits"]["analyses_per_month"] == 500
    assert c.post("/api/v1/billing/checkout", headers=h, json={"plan": "team"}).status_code == 409
    assert c.post("/api/v1/billing/cancel", headers=h).json()["status"] == "cancelling"
    assert fake.cancelled == ["sub_123"]
    hook(c, "subscription.cancelled", event_id="evt_2")
    assert c.get("/api/v1/billing", headers=h).json()["plan"] == "free"


def test_webhook_rejects_bad_signature_and_is_idempotent(env):
    c, _ = env
    h = hdr(c)
    c.post("/api/v1/billing/checkout", headers=h, json={"plan": "team"})
    assert hook(c, "subscription.activated", secret="wrong").status_code == 401
    assert c.get("/api/v1/billing", headers=h).json()["plan"] == "free"
    assert hook(c, "subscription.activated").status_code == 200
    assert hook(c, "subscription.activated").json() == {"duplicate": True}


def test_billed_revenue_feeds_command_center(env):
    c, _ = env
    boss, dev = hdr(c, "boss@x.io"), hdr(c)
    c.post("/api/v1/billing/checkout", headers=dev, json={"plan": "team"})
    hook(c, "subscription.activated")
    o = c.get("/api/v1/admin/overview", headers=boss).json()
    assert o["mrr_inr"] == 4999 and o["paying_teams"] == 1 and o["milestones"][0]["reached"] is True


def test_checkout_unconfigured_and_validation(env, monkeypatch):
    c, _ = env
    h = hdr(c)
    assert c.post("/api/v1/billing/checkout", headers=h, json={"plan": "enterprise"}).status_code == 422
    monkeypatch.setattr(config.settings, "razorpay_plan_pro", "")
    assert c.post("/api/v1/billing/checkout", headers=h, json={"plan": "pro"}).status_code == 503


def test_github_install_state_is_signed_and_callback_connects(env):
    c, _ = env
    h = hdr(c)
    url = c.get("/api/v1/integrations/github/install-url", headers=h).json()["url"]
    state = url.split("state=")[1]
    ok = c.get(f"/api/v1/integrations/github/callback?installation_id=777&state={state}", follow_redirects=False)
    assert ok.status_code == 302 and ok.headers["location"].endswith("github=connected")
    bad = c.get("/api/v1/integrations/github/callback?installation_id=777&state=forged", follow_redirects=False)
    assert bad.headers["location"].endswith("github=invalid")
    assert jwt.decode(state, config.settings.jwt_secret, algorithms=["HS256"])["org"]
