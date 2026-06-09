from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import health, telegram
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Extella Sales Hub starting...")
    logger.info(f"Environment: {settings.app_env}")
    yield
    logger.info("Extella Sales Hub shutting down")


app = FastAPI(
    title="Extella Sales Hub",
    description="AI-powered B2B Sales Management Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(health.router)
app.include_router(telegram.router, prefix="/webhook")
