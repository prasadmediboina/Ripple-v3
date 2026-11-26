"""GitHub App connection flow: install -> callback (Setup URL) -> choose repositories."""
import time

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import Ctx, get_ctx, get_db
from ..models import Integration
from ..service import audit
from ..sources import GitHubProvider

router = APIRouter(prefix="/integrations/github", tags=["github"])


@router.get("/install-url")
def install_url(ctx: Ctx = Depends(get_ctx)):
    if not settings.github_app_slug:
        raise HTTPException(503, "GitHub App is not configured on this deployment yet.")
    state = jwt.encode({"org": ctx.org.id, "exp": int(time.time()) + 900}, settings.jwt_secret, algorithm="HS256")
    return {"url": f"https://github.com/apps/{settings.github_app_slug}/installations/new?state={state}"}


@router.get("/callback")
def callback(installation_id: str = "", state: str = "", db: Session = Depends(get_db)):
    """GitHub redirects the browser here after install ('Setup URL'). The signed state ties it to the team."""
    try:
        org_id = jwt.decode(state, settings.jwt_secret, algorithms=["HS256"])["org"]
    except jwt.PyJWTError:
        return RedirectResponse(f"{settings.frontend_url}/dashboard?github=invalid", status_code=302)
    if not installation_id.isdigit():
        return RedirectResponse(f"{settings.frontend_url}/dashboard?github=invalid", status_code=302)
    if not db.scalar(select(Integration).where(Integration.organization_id == org_id, Integration.installation_id == installation_id)):
        db.add(Integration(organization_id=org_id, provider="github", installation_id=installation_id))
        audit(db, org_id, None, "integration.connected", f"github:{installation_id}")
        db.commit()
    return RedirectResponse(f"{settings.frontend_url}/dashboard?github=connected", status_code=302)


@router.get("/available-repos")
def available_repos(ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    integ = db.scalar(select(Integration).where(Integration.organization_id == ctx.org.id, Integration.provider == "github",
                                                 Integration.installation_id.is_not(None)).order_by(Integration.id.desc()))
    if not integ:
        return {"installation_id": None, "repositories": []}
    try:
        repos = GitHubProvider().list_repositories(integ.installation_id)
    except Exception:
        raise HTTPException(502, "Could not list repositories from GitHub. Check the GitHub App settings.")
    return {"installation_id": integ.installation_id, "repositories": repos}
