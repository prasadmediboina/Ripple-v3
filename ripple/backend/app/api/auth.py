import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import Ctx, get_ctx, get_db
from ..models import Membership, Organization, Subscription, User
from ..security import create_token, hash_password, verify_password
from ..service import audit

router = APIRouter(prefix="/auth", tags=["auth"])
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=10, max_length=200)
    organization_name: str | None = None


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(422, "Enter a valid email address")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    user = User(email=email, password_hash=hash_password(body.password))
    org = Organization(name=body.organization_name or email.split("@")[0])
    db.add_all([user, org])
    db.flush()
    db.add_all([Membership(user_id=user.id, organization_id=org.id, role="owner"),
                Subscription(organization_id=org.id, plan="free")])
    audit(db, org.id, user.id, "user.registered")
    db.commit()
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@router.get("/me")
def me(ctx: Ctx = Depends(get_ctx)):
    return {"id": ctx.user.id, "email": ctx.user.email, "is_admin": ctx.user.email in settings.admin_emails, "organization": {
        "id": ctx.org.id, "name": ctx.org.name, "plan": ctx.org.plan, "role": ctx.role}}
