from __future__ import annotations

from fastapi import APIRouter, Depends, BackgroundTasks

from api.deps import require_user
from core.models import RunStatus
from schemas import PipelineRunResponse, TriggerRunRequest
from services.pipeline_service import PipelineService

router = APIRouter(prefix='/api/runs', tags=['runs'])


@router.post('/trigger', response_model=PipelineRunResponse)
async def trigger_run(
    background_tasks: BackgroundTasks,
    payload: TriggerRunRequest,
    _user=Depends(require_user),
) -> PipelineRunResponse:
    pipeline = PipelineService()
    
    # Check if already locked before launching background task
    if pipeline._run_lock.locked():
        return PipelineRunResponse(
            run_id=0,
            status=RunStatus.skipped,
            ingested_count=0,
            candidates_count=0,
            drafts_count=0,
            reason='already_running'
        )

    # Launch in background
    background_tasks.add_task(pipeline.run, trigger_source=payload.trigger_source)
    
    return PipelineRunResponse(
        run_id=0,
        status=RunStatus.pending,
        ingested_count=0,
        candidates_count=0,
        drafts_count=0,
        reason='started_in_background'
    )
