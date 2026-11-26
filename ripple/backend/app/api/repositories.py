from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import Ctx, get_ctx, get_db, owned_repo
from ..models import CodeNodeRow, DependencyRow, Integration, Repository
from ..security import encrypt_secret
from ..service import LimitExceeded, audit, check_repo_quota, index_repository

router = APIRouter(tags=["repositories"])


class ConnectIn(BaseModel):
    installation_id: str
    access_token: str | None = None   # optional; stored encrypted. GitHub App tokens are minted on demand.


class RepoIn(BaseModel):
    name: str
    full_name: str | None = None
    github_id: str | None = None
    installation_id: str | None = None
    local_path: str | None = None


class IndexIn(BaseModel):
    ref: str = "HEAD"


def _out(r: Repository) -> dict:
    return {"id": r.id, "name": r.name, "full_name": r.full_name, "last_indexed_sha": r.last_indexed_sha,
            "source": "local" if r.local_path else "github"}


@router.post("/integrations/github/connect", status_code=201)
def connect_github(body: ConnectIn, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    db.add(Integration(organization_id=ctx.org.id, provider="github", installation_id=body.installation_id,
                       encrypted_token=encrypt_secret(body.access_token) if body.access_token else None))
    audit(db, ctx.org.id, ctx.user.id, "integration.connected", f"github:{body.installation_id}")
    db.commit()
    return {"connected": True}


@router.get("/repositories")
def list_repositories(ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    rows = db.scalars(select(Repository).where(Repository.organization_id == ctx.org.id)).all()
    return [_out(r) for r in rows]


@router.post("/repositories", status_code=201)
def add_repository(body: RepoIn, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    if body.local_path and not settings.allow_local_repos:
        raise HTTPException(403, "Local repositories are disabled on this deployment")
    try:
        check_repo_quota(db, ctx.org)
    except LimitExceeded as e:
        raise HTTPException(402, str(e))
    repo = Repository(organization_id=ctx.org.id, name=body.name, full_name=body.full_name,
                      github_id=body.github_id, installation_id=body.installation_id, local_path=body.local_path)
    db.add(repo)
    audit(db, ctx.org.id, ctx.user.id, "repository.added", body.name)
    db.commit()
    return _out(repo)


@router.post("/repositories/{repo_id}/index")
def index(repo_id: str, body: IndexIn, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    repo = owned_repo(db, ctx, repo_id)
    try:
        return index_repository(db, repo, body.ref)
    except (PermissionError, ValueError) as e:
        raise HTTPException(400, str(e))


@router.get("/repositories/{repo_id}/graph")
def graph(repo_id: str, ctx: Ctx = Depends(get_ctx), db: Session = Depends(get_db)):
    repo = owned_repo(db, ctx, repo_id)
    nodes = db.scalars(select(CodeNodeRow).where(CodeNodeRow.repository_id == repo.id)).all()
    edges = db.scalars(select(DependencyRow).where(DependencyRow.repository_id == repo.id)).all()
    return {"commit": repo.last_indexed_sha,
            "nodes": [{"id": n.node_id, "name": n.name, "file": n.file_path, "type": n.node_type, "is_test": n.is_test}
                      for n in nodes if n.node_type != "module"],
            "edges": [{"source": e.source_id, "target": e.target_id, "relation": e.relation,
                       "evidence": e.evidence, "resolution": e.resolution} for e in edges]}
