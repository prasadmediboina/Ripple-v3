import pytest
from fastapi.testclient import TestClient

from app import config, db as dbmod
from app.engine import analyze_snapshots
from app.engine.reviewers import suggest_reviewers


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(config.settings, "admin_emails", ["boss@x.io"])
    eng = dbmod.make_engine("sqlite:///:memory:")
    dbmod.SessionLocal.configure(bind=eng)
    from app.models import Base
    Base.metadata.create_all(eng)
    from app.main import app
    return TestClient(app)


def reg(c, email):
    t = c.post("/api/v1/auth/register", json={"email": email, "password": "correct-horse-1"}).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


def test_risk_is_explainable_and_scales(shop_files):
    head = dict(shop_files)
    head["shop/payments.py"] = head["shop/payments.py"].replace('"paid"', '"ok"')
    r = analyze_snapshots(shop_files, head).to_dict()["risk"]
    assert 0 < r["score"] <= 100 and r["level"] in ("low", "moderate", "elevated", "high")
    assert sum(f["points"] for f in r["factors"]) == r["score"]          # every point is accounted for
    calm = analyze_snapshots(shop_files, shop_files).to_dict()["risk"]
    assert calm["score"] == 0 and r["score"] > calm["score"]


def test_reviewer_ranking():
    authors = {"a.py": {"ana": 5, "raj": 1}, "b.py": {"raj": 4}, "c.py": {"raj": 2, "ana": 1}}
    top = suggest_reviewers(authors, ["a.py", "b.py", "c.py"])
    assert top[0]["author"] == "raj" and top[0]["files_covered"] == 3


def test_admin_is_founder_only(client):
    boss, other = reg(client, "boss@x.io"), reg(client, "dev@x.io")
    assert client.get("/api/v1/admin/overview", headers=other).status_code == 403
    assert client.get("/api/v1/auth/me", headers=boss).json()["is_admin"] is True
    assert client.get("/api/v1/auth/me", headers=other).json()["is_admin"] is False
    o = client.get("/api/v1/admin/overview", headers=boss).json()
    assert o["users"] == 2 and o["paying_teams"] == 0 and o["mrr_inr"] == 0


def test_manual_plan_change_is_comped_not_revenue(client):
    boss = reg(client, "boss@x.io"); reg(client, "dev@x.io")
    orgs = client.get("/api/v1/admin/organizations", headers=boss).json()
    target = next(o for o in orgs if o["name"] == "dev")
    assert client.patch(f"/api/v1/admin/organizations/{target['id']}/plan", headers=boss, json={"plan": "team"}).status_code == 200
    o = client.get("/api/v1/admin/overview", headers=boss).json()
    assert o["mrr_inr"] == 0 and o["paying_teams"] == 0 and o["comped_teams"] == 1      # hand-set plans are comped, not billed
    assert o["list_price_mrr_inr"] == 4999 and o["milestones"][0]["reached"] is False
    assert client.patch(f"/api/v1/admin/organizations/{target['id']}/plan", headers=boss, json={"plan": "gold"}).status_code == 422
    assert any(a["action"] == "admin.plan_changed" for a in client.get("/api/v1/admin/audit", headers=boss).json())


def test_lead_pipeline(client):
    boss = reg(client, "boss@x.io")
    l = client.post("/api/v1/admin/leads", headers=boss, json={"name": "Asha", "company": "Acme"}).json()
    assert client.patch(f"/api/v1/admin/leads/{l['id']}", headers=boss, json={"stage": "interviewed"}).json()["stage"] == "interviewed"
    assert client.patch(f"/api/v1/admin/leads/{l['id']}", headers=boss, json={"stage": "nope"}).status_code == 422
    assert client.get("/api/v1/admin/overview", headers=boss).json()["leads"] == {"interviewed": 1}
    assert client.delete(f"/api/v1/admin/leads/{l['id']}", headers=boss).status_code == 204
