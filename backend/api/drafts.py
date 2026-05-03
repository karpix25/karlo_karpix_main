from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import require_user
from core.models import DraftStatus
from core.repository import get_draft, list_drafts, set_draft_status, update_draft
from schemas import DraftActionResponse, DraftItem, DraftUpdateRequest
from services.content_regen_service import regenerate_draft
from services.draft_service import DraftService

router = APIRouter(prefix='/api/drafts', tags=['drafts'])


@router.get('', response_model=list[DraftItem])
async def get_drafts(
    platform: str | None = Query(default=None),
    status: str | None = Query(default=None),
    _user=Depends(require_user),
) -> list[DraftItem]:
    rows = await list_drafts(platform=platform, status=status)
    return [DraftItem(**row) for row in rows]


@router.get('/{draft_id}', response_model=DraftItem)
async def get_draft_by_id(draft_id: int, _user=Depends(require_user)) -> DraftItem:
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail='draft_not_found')
    return DraftItem(**draft)


@router.put('/{draft_id}', response_model=DraftItem)
async def update_draft_by_id(
    draft_id: int,
    payload: DraftUpdateRequest,
    _user=Depends(require_user),
) -> DraftItem:
    existing = await get_draft(draft_id)
    if not existing:
        raise HTTPException(status_code=404, detail='draft_not_found')

    await update_draft(
        draft_id,
        content=payload.content,
        cta=payload.cta,
        hashtags=payload.hashtags,
    )
    refreshed = await get_draft(draft_id)
    if not refreshed:
        raise HTTPException(status_code=404, detail='draft_not_found')
    return DraftItem(**refreshed)


@router.post('/{draft_id}/approve', response_model=DraftActionResponse)
async def approve_draft(draft_id: int, _user=Depends(require_user)) -> DraftActionResponse:
    service = DraftService()
    try:
        status, publish_result = await service.approve(draft_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return DraftActionResponse(id=draft_id, status=status, publish_result=publish_result)


@router.post('/{draft_id}/reject', response_model=DraftActionResponse)
async def reject_draft(draft_id: int, _user=Depends(require_user)) -> DraftActionResponse:
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail='draft_not_found')

    await set_draft_status(draft_id, DraftStatus.rejected)
    return DraftActionResponse(id=draft_id, status=DraftStatus.rejected)


@router.post('/{draft_id}/regenerate', response_model=DraftItem)
async def regenerate_draft_by_id(draft_id: int, _user=Depends(require_user)) -> DraftItem:
    draft = await regenerate_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail='draft_not_found')
    return DraftItem(**draft)


@router.post('/generate-digest', response_model=DraftItem)
async def generate_digest_draft(hours: int = 24, _user=Depends(require_user)) -> DraftItem:
    from core.repository import list_accepted_candidates, create_draft, get_draft
    from agents.content_orchestrator import ContentOrchestratorAgent
    from core.models import DraftPlatform, DraftStatus
    
    items = await list_accepted_candidates(hours=hours)
    if not items:
        raise HTTPException(status_code=400, detail="no_accepted_items_found")
    
    agent = ContentOrchestratorAgent()
    generated = await agent.generate_digest(items)
    
    # Use the first item's ID as the primary anchor for the digest draft
    anchor_id = items[0]['id']
    
    draft_id = await create_draft(
        candidate_id=anchor_id,
        platform=DraftPlatform.digest,
        content=generated.content,
        cta=generated.cta,
        hashtags=generated.hashtags,
        status=DraftStatus.in_review
    )
    
    draft = await get_draft(draft_id)
    return DraftItem(**draft)
