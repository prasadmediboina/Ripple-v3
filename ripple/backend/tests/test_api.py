import hashlib
import hmac
import json
import subprocess

import pytest
from fastapi.testclient import TestClient

from app import config, db as dbmod


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "allow_local_repos", True)
    monkeypatch.setattr(config.settings, "github_webhook_secret", "whsec")
    eng = dbmod.make_engine("sqlite:///:memory:")
    dbmod.SessionLocal.configure(bind=eng)
    from app.models import Base
    Base.metadata.create_all(eng)
    from app.main import app
    return TestClient(app)


def git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)


@pytest.fixture
def git_repo(tmp_path, shop_files):
    repo = tmp_path / "shop_repo"
    repo.mkdir()
    git(repo, "init", "-q"); git(repo, "config", "user.email", "t@t.io"); git(repo, "config", "user.name", "t")
    for p, s in shop_files.items():
        f = repo / p; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(s)
    git(repo, "add", "."); git(repo, "commit", "-qm", "base")
    base = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    pay = repo / "shop/payments.py"
    pay.write_text(pay.read_text().replace('"paid"', '"ok"'))
    git(repo, "commit", "-qam", "change payment")
    head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return repo, base, head


def auth(client, email="a@x.io"):
    t = client.post("/api/v1/auth/register", json={"email": email, "password": "correct-horse-1"}).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


def test_end_to_end_analysis(client, git_repo):
    repo, base, head = git_repo
    h = auth(client)
    r = client.post("/api/v1/repositories", headers=h, json={"name": "shop", "local_path": str(repo)}).json()
    idx = client.post(f"/api/v1/repositories/{r['id']}/index", headers=h, json={"ref": head}).json()
    assert idx["nodes"] > 5 and idx["edges"] > 3
    assert client.get(f"/api/v1/repositories/{r['id']}/graph", headers=h).json()["edges"]
    pr = client.post("/api/v1/pull-requests", headers=h, json={
        "repository_id": r["id"], "pr_number": 7, "base_sha": base, "head_sha": head, "title": "Tweak payments"}).json()
    aid = client.post(f"/api/v1/pull-requests/{pr['id']}/analyze", headers=h).json()["analysis_id"]
    a = client.get(f"/api/v1/analyses/{aid}", headers=h).json()
    assert a["status"] == "complete", a
    assert a["report"]["summary"]["potentially_affected"] >= 4
    f = client.get(f"/api/v1/analyses/{aid}/findings", headers=h).json()
    assert f and f[0]["explanation"]
    assert client.post("/api/v1/feedback", headers=h, json={"analysis_id": aid, "finding_id": f[0]["id"], "outcome": "confirmed"}).status_code == 201
    d = client.get("/api/v1/dashboard", headers=h).json()
    assert d["analyses_completed"] == 1 and d["measured_precision"] == 1.0
    assert client.get("/api/v1/usage", headers=h).json()["analyses"] == 1


def test_organization_isolation(client, git_repo):
    repo, base, head = git_repo
    h1, h2 = auth(client, "one@x.io"), auth(client, "two@x.io")
    r = client.post("/api/v1/repositories", headers=h1, json={"name": "shop", "local_path": str(repo)}).json()
    assert client.get(f"/api/v1/repositories/{r['id']}/graph", headers=h2).status_code == 404
    assert client.get("/api/v1/repositories", headers=h2).json() == []


def test_free_plan_repo_limit(client, git_repo):
    repo, *_ = git_repo
    h = auth(client)
    assert client.post("/api/v1/repositories", headers=h, json={"name": "a", "local_path": str(repo)}).status_code == 201
    assert client.post("/api/v1/repositories", headers=h, json={"name": "b", "local_path": str(repo)}).status_code == 402


def test_auth_required_and_login(client):
    assert client.get("/api/v1/repositories").status_code == 401
    auth(client, "l@x.io")
    assert client.post("/api/v1/auth/login", json={"email": "l@x.io", "password": "wrong-password"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "l@x.io", "password": "correct-horse-1"}).status_code == 200


def test_webhook_signature_is_verified(client):
    body = json.dumps({"action": "opened"}).encode()
    assert client.post("/api/v1/webhooks/github", content=body, headers={"X-GitHub-Event": "pull_request"}).status_code == 401
    sig = "sha256=" + hmac.new(b"whsec", body, hashlib.sha256).hexdigest()
    ok = client.post("/api/v1/webhooks/github", content=body, headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": sig})
    assert ok.status_code == 202


def test_secrets_are_encrypted_at_rest():
    from app.security import decrypt_secret, encrypt_secret
    enc = encrypt_secret("ghs_secret")
    assert "ghs_secret" not in enc and decrypt_secret(enc) == "ghs_secret"
