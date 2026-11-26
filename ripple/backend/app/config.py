import os
from dataclasses import dataclass, field


def _db_url(url: str) -> str:
    # Render/Heroku give postgres:// or postgresql://; SQLAlchemy + psycopg3 needs the +psycopg driver tag.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def _b(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes")


@dataclass
class Settings:
    env: str = field(default_factory=lambda: os.getenv("RIPPLE_ENV", "development"))
    database_url: str = field(default_factory=lambda: _db_url(os.getenv("DATABASE_URL", "sqlite:///./ripple.db")))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-only-change-me"))
    encryption_key: str = field(default_factory=lambda: os.getenv("ENCRYPTION_KEY", ""))   # Fernet key
    github_app_id: str = field(default_factory=lambda: os.getenv("GITHUB_APP_ID", ""))
    github_app_private_key: str = field(default_factory=lambda: os.getenv("GITHUB_APP_PRIVATE_KEY", ""))
    github_webhook_secret: str = field(default_factory=lambda: os.getenv("GITHUB_WEBHOOK_SECRET", ""))
    queue_backend: str = field(default_factory=lambda: os.getenv("QUEUE_BACKEND", "inline"))  # inline | celery
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    allow_local_repos: bool = field(default_factory=lambda: _b("ALLOW_LOCAL_REPOS"))   # dev/self-hosted only
    admin_emails: list[str] = field(default_factory=lambda: [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()])
    frontend_url: str = field(default_factory=lambda: os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/"))
    razorpay_key_id: str = field(default_factory=lambda: os.getenv("RAZORPAY_KEY_ID", ""))
    razorpay_key_secret: str = field(default_factory=lambda: os.getenv("RAZORPAY_KEY_SECRET", ""))
    razorpay_webhook_secret: str = field(default_factory=lambda: os.getenv("RAZORPAY_WEBHOOK_SECRET", ""))
    razorpay_plan_pro: str = field(default_factory=lambda: os.getenv("RAZORPAY_PLAN_PRO", ""))
    razorpay_plan_team: str = field(default_factory=lambda: os.getenv("RAZORPAY_PLAN_TEAM", ""))
    github_app_slug: str = field(default_factory=lambda: os.getenv("GITHUB_APP_SLUG", ""))
    post_pr_comments: bool = field(default_factory=lambda: _b("POST_PR_COMMENTS", "true"))
    cors_origins: list[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","))

    def validate_for_production(self) -> None:
        if self.env == "production":
            missing = [n for n, v in (("JWT_SECRET", self.jwt_secret != "dev-only-change-me"),
                                      ("ENCRYPTION_KEY", bool(self.encryption_key))) if not v]
            if missing:
                raise RuntimeError(f"Missing required production settings: {', '.join(missing)}")
            if self.allow_local_repos:
                raise RuntimeError("ALLOW_LOCAL_REPOS must be off in production")


settings = Settings()
