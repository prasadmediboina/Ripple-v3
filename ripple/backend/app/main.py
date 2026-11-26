from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api import admin, analyses, auth, billing, github, repositories, webhooks
from .config import settings
from .db import engine
from .models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_for_production()
    Base.metadata.create_all(engine)   # use Alembic migrations once the schema stabilises
    yield


app = FastAPI(title="RIPPLE API", version=__version__, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])

for r in (auth.router, repositories.router, analyses.router, webhooks.router, admin.router, billing.router, github.router):
    app.include_router(r, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}
