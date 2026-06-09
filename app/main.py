from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import health, telegram
from app.routers import dashboard, auth, admin
from app.config import settings
import app.db as db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Extella Sales Hub starting...")
    logger.info(f"Environment: {settings.app_env}")
    # Ensure admin user exists on every startup
    try:
        if settings.admin_email and settings.secret_key:
            # Admin password stored separately - use env var ADMIN_PASSWORD if set,
            # otherwise admin must set password via invite flow
            import os
            admin_pw = os.environ.get("ADMIN_PASSWORD", "")
            if admin_pw:
                db.ensure_admin(settings.admin_email, db.hash_pw(admin_pw))
                logger.info(f"Admin user ensured: {settings.admin_email}")
    except Exception as e:
        logger.warning(f"ensure_admin failed (non-critical): {e}")
    yield
    logger.info("Extella Sales Hub shutting down")


app = FastAPI(
    title="Extella Sales Hub",
    description="AI-powered B2B Sales Management Platform",
    version="2.0.0",
    lifespan=lifespan
)

# Auth & pages
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

# API & bots
app.include_router(health.router)
app.include_router(telegram.router, prefix="/webhook")
