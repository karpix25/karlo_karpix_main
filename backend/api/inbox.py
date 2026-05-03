from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException

from api.deps import require_user
from schemas import InboxItem, FormatDecisionRequest
from core.repository import list_inbox, record_user_decision, create_draft
from core.models import DraftPlatform, DraftStatus
from agents.content_orchestrator import ContentOrchestratorAgent

router = APIRouter(prefix='/api/inbox', tags=['inbox'])
agent = ContentOrchestratorAgent()


@router.get('', response_model=list[InboxItem])
async def get_inbox(
    status: str | None = Query(default=None),
    _user=Depends(require_user),
) -> list[InboxItem]:
    rows = await list_inbox(status=status)
    return [InboxItem(**row) for row in rows]

@router.post('/{candidate_id}/decision')
async def post_decision(
    candidate_id: int,
    request: FormatDecisionRequest,
    _user=Depends(require_user),
):
    rows = await list_inbox()
    candidate = next((r for r in rows if r['candidate_id'] == candidate_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    generated = await agent.generate_draft(
        platform=request.chosen_format,
        summary=candidate['summary'],
        source_text=candidate['text']
    )
    
    await record_user_decision(
        candidate_id=candidate_id,
        original_text=candidate['text'],
        original_media_type=candidate.get('media_type'),
        chosen_format=request.chosen_format,
        generated_content=generated.content
    )
    
    platform_enum = DraftPlatform.telegram
    try:
        platform_enum = DraftPlatform(request.chosen_format)
    except ValueError:
        pass

    await create_draft(
        candidate_id=candidate_id,
        platform=platform_enum,
        content=generated.content,
        cta=generated.cta,
        hashtags=generated.hashtags,
        status=DraftStatus.in_review,
    )
    
    return {"status": "ok", "generated_content": generated.content}
