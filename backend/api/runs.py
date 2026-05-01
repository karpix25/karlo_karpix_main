from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import require_user
from schemas import PipelineRunResponse, TriggerRunRequest
from services.pipeline_service import PipelineService

router = APIRouter(prefix='/api/runs', tags=['runs'])


@router.post('/trigger', response_model=PipelineRunResponse)
async def trigger_run(
    payload: TriggerRunRequest,
    _user=Depends(require_user),
) -> PipelineRunResponse:
    pipeline = PipelineService()
    result = await pipeline.run(trigger_source=payload.trigger_source)
    return PipelineRunResponse(**result)
