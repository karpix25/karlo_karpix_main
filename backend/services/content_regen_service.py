from __future__ import annotations

from agents.content_orchestrator import ContentOrchestratorAgent
from core.models import DraftPlatform, DraftStatus
from core.repository import get_draft, update_draft


async def regenerate_draft(draft_id: int) -> dict | None:
    draft = await get_draft(draft_id)
    if not draft:
        return None

    agent = ContentOrchestratorAgent()
    platform = DraftPlatform(draft['platform'])

    regenerated = await agent.generate_draft(
        platform=platform.value,
        summary='Regenerated draft based on previous version',
        source_text=draft['content'],
    )

    await update_draft(
        draft_id,
        content=regenerated.content,
        cta=regenerated.cta,
        hashtags=regenerated.hashtags,
    )

    # Keep regenerated drafts in review queue.
    from core.repository import set_draft_status

    await set_draft_status(draft_id, DraftStatus.in_review)
    return await get_draft(draft_id)
