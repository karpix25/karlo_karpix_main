from __future__ import annotations

import pytest

from core.database import init_db
from core.models import RunStatus
from core.repository import release_runtime_lock, try_acquire_runtime_lock
from services.pipeline_service import PipelineService


@pytest.mark.asyncio
async def test_pipeline_returns_skipped_when_lock_is_held() -> None:
    await init_db()
    service = PipelineService()

    await PipelineService._run_lock.acquire()
    try:
        result = await service.run(trigger_source='manual')
    finally:
        if PipelineService._run_lock.locked():
            PipelineService._run_lock.release()

    assert result['status'] == RunStatus.skipped.value
    assert result['reason'] == 'already_running'
    assert result['run_id'] == 0


@pytest.mark.asyncio
async def test_pipeline_returns_skipped_when_db_lock_is_held() -> None:
    await init_db()
    service = PipelineService()

    acquired = await try_acquire_runtime_lock('pipeline_run', 'other-owner', 3600)
    assert acquired is True

    try:
        result = await service.run(trigger_source='manual')
    finally:
        await release_runtime_lock('pipeline_run', 'other-owner')

    assert result['status'] == RunStatus.skipped.value
    assert result['reason'] == 'already_running'
    assert result['run_id'] == 0
