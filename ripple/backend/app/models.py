from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(200))
    plan: Mapped[str] = mapped_column(String(20), default="free")
    llm_consent: Mapped[bool] = mapped_column(default=False)   # explicit opt-in before any LLM use


class Membership(Base):
    __tablename__ = "memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), default="owner")   # owner | admin | member


class Integration(Base):
    __tablename__ = "integrations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20), default="github")
    installation_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    encrypted_token: Mapped[str | None] = mapped_column(Text, nullable=True)


class Repository(Base):
    __tablename__ = "repositories"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    full_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    github_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    installation_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_indexed_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CodeNodeRow(Base):
    __tablename__ = "code_nodes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    commit_sha: Mapped[str] = mapped_column(String(64))
    node_id: Mapped[str] = mapped_column(String(600))
    name: Mapped[str] = mapped_column(String(300))
    file_path: Mapped[str] = mapped_column(String(600))
    node_type: Mapped[str] = mapped_column(String(20))
    is_test: Mapped[bool] = mapped_column(default=False)


class DependencyRow(Base):
    __tablename__ = "dependencies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    commit_sha: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[str] = mapped_column(String(600))
    target_id: Mapped[str] = mapped_column(String(600))
    relation: Mapped[str] = mapped_column(String(20))
    evidence: Mapped[str] = mapped_column(Text)
    resolution: Mapped[str] = mapped_column(String(12), default="exact")


class PullRequest(Base):
    __tablename__ = "pull_requests"
    __table_args__ = (UniqueConstraint("repository_id", "pr_number"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), index=True)
    pr_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500), default="")
    base_sha: Mapped[str] = mapped_column(String(64))
    head_sha: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="open")


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    pull_request_id: Mapped[str] = mapped_column(ForeignKey("pull_requests.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")   # queued|running|complete|failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImpactFindingRow(Base):
    __tablename__ = "impact_findings"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    changed_node_id: Mapped[str] = mapped_column(String(600))
    affected_node_id: Mapped[str] = mapped_column(String(600))
    confidence: Mapped[str] = mapped_column(String(10))
    depth: Mapped[int] = mapped_column(Integer)
    evidence: Mapped[dict] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text, default="")


class TestRecommendationRow(Base):
    __tablename__ = "test_recommendations"
    __test__ = False
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    test_node_id: Mapped[str] = mapped_column(String(600))
    reason: Mapped[str] = mapped_column(Text)


class AnalysisFeedback(Base):
    __tablename__ = "analysis_feedback"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    finding_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    outcome: Mapped[str] = mapped_column(String(20))   # confirmed | false_positive | missed_impact
    note: Mapped[str] = mapped_column(Text, default="")


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (UniqueConstraint("organization_id", "metric", "period"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    metric: Mapped[str] = mapped_column(String(40))
    period: Mapped[str] = mapped_column(String(7))   # YYYY-MM
    quantity: Mapped[int] = mapped_column(Integer, default=0)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), unique=True)
    plan: Mapped[str] = mapped_column(String(20), default="free")
    status: Mapped[str] = mapped_column(String(20), default="active")
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)   # e.g. Razorpay / Stripe


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Lead(Base):
    """Founder CRM: customer-discovery pipeline."""
    __tablename__ = "leads"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200), default="")
    contact: Mapped[str] = mapped_column(String(300), default="")
    stage: Mapped[str] = mapped_column(String(20), default="identified")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class BillingEvent(Base):
    """Processed payment-provider webhooks, for idempotency (providers retry)."""
    __tablename__ = "billing_events"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    event: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
