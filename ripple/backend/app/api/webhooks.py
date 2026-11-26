import json

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_db
from ..models import Organization, PullRequest, Repository
from ..security import verify_github_signature
from ..service import LimitExceeded
from .analyses import create_analysis

router = APIRouter(tags=["webhooks"])
ACTIONS = {"opened", "synchronize", "reopened"}


@router.post("/webhooks/github", status_code=202)
async def github_webhook(request: Request, background: BackgroundTasks, db: Session = Depends(get_db),
                         x_hub_signature_256: str | None = Header(default=None),
                         x_github_event: str | None = Header(default=None)):
    body = await request.body()
    if not verify_github_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        raise HTTPException(401, "Invalid webhook signature")
    if x_github_event != "pull_request":
        return {"ignored": x_github_event}
    p = json.loads(body)
    if p.get("action") not in ACTIONS:
        return {"ignored": p.get("action")}
    gh_id = (p.get("repository") or {}).get("id")
    pr_data = p.get("pull_request")
    if gh_id is None or not pr_data:
        return {"ignored": "unsupported payload"}
    repo = db.scalar(select(Repository).where(Repository.github_id == str(gh_id)))
    if not repo:
        return {"ignored": "repository not connected"}
    pr = db.scalar(select(PullRequest).where(PullRequest.repository_id == repo.id, PullRequest.pr_number == pr_data["number"]))
    if not pr:
        pr = PullRequest(repository_id=repo.id, pr_number=pr_data["number"], base_sha="", head_sha="")
        db.add(pr)
    pr.title, pr.base_sha, pr.head_sha = pr_data["title"], pr_data["base"]["sha"], pr_data["head"]["sha"]
    db.commit()
    try:   # respond immediately; the heavy work runs in the background queue
        a = create_analysis(db, db.get(Organization, repo.organization_id), pr, background)
    except LimitExceeded as e:
        return {"skipped": str(e)}
    return {"analysis_id": a.id}
