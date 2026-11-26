from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Membership, Organization, Repository, User
from .security import decode_token


def get_db():
    with SessionLocal() as db:
        yield db


@dataclass
class Ctx:
    user: User
    org: Organization
    role: str


def get_ctx(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> Ctx:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    uid = decode_token(authorization.split(" ", 1)[1])
    user = db.get(User, uid) if uid else None
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    m = db.scalar(select(Membership).where(Membership.user_id == user.id))
    if not m:
        raise HTTPException(403, "User has no organization")
    return Ctx(user=user, org=db.get(Organization, m.organization_id), role=m.role)


def owned_repo(db: Session, ctx: Ctx, repo_id: str) -> Repository:
    """Org-level isolation: a repository is only visible inside its own organization."""
    repo = db.scalar(select(Repository).where(Repository.id == repo_id, Repository.organization_id == ctx.org.id))
    if not repo:
        raise HTTPException(404, "Repository not found")
    return repo
