from __future__ import annotations

from core.models import DraftPlatform, DraftStatus
from core.repository import get_draft, set_draft_status
from services.telethon_service import TelethonUserbotService


class DraftService:
    def __init__(self) -> None:
        self.userbot = TelethonUserbotService()

    async def approve(self, draft_id: int) -> tuple[DraftStatus, str | None]:
        draft = await get_draft(draft_id)
        if not draft:
            raise ValueError('draft_not_found')

        platform = DraftPlatform(draft['platform'])
        if platform == DraftPlatform.telegram:
            publish_url = await self.userbot.publish_to_telegram('carlo_channel', draft['content'])
            await set_draft_status(draft_id, DraftStatus.published, publish_result=publish_url)
            return DraftStatus.published, publish_url

        export_block = '\n'.join(
            [
                draft['content'],
                '',
                f"CTA: {draft.get('cta') or ''}",
                f"Hashtags: {draft.get('hashtags') or ''}",
            ]
        )
        await set_draft_status(
            draft_id,
            DraftStatus.ready_for_manual_publish,
            publish_result=export_block,
        )
        return DraftStatus.ready_for_manual_publish, export_block

    async def reject(self, draft_id: int) -> DraftStatus:
        await set_draft_status(draft_id, DraftStatus.rejected)
        return DraftStatus.rejected
