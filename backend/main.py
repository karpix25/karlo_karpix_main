from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.drafts import router as drafts_router
from api.inbox import router as inbox_router
from api.runs import router as runs_router
from api.settings import router as settings_router
from core.config import get_settings
from core.database import init_db
from services.scheduler_service import PipelineScheduler

scheduler = PipelineScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(runs_router)
app.include_router(inbox_router)
app.include_router(drafts_router)
app.include_router(settings_router)


@app.get('/health')
async def healthcheck() -> dict[str, str]:
    return {'status': 'ok'}
