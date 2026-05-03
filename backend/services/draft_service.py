from __future__ import annotations

from core.models import DraftPlatform, DraftStatus
from core.repository import get_draft, set_draft_status
from services.telethon_service import TelethonUserbotService


class DraftService:
    def __init__(self) -> None:
        self.userbot = TelethonUserbotService()

    async def approve(self, draft_id: int) -> tuple[DraftStatus, str | None]:
        from core.repository import get_setting
        draft = await get_draft(draft_id)
        if not draft:
            raise ValueError('draft_not_found')

        pub_settings = await get_setting('publishing')
        target_channel = pub_settings.get('telegram_target_channel') or 'carlo_channel'
        telegraph_token = pub_settings.get('telegraph_access_token')

        platform = DraftPlatform(draft['platform'])
        if platform == DraftPlatform.telegram or platform == DraftPlatform.digest:
            publish_url = await self.userbot.publish_to_telegram(target_channel, draft['content'])
            await set_draft_status(draft_id, DraftStatus.published, publish_result=publish_url)
            return DraftStatus.published, publish_url

        if platform == DraftPlatform.telegraph:
            from services.telegraph_service import TelegraphService
            t_service = TelegraphService(access_token=telegraph_token)
            lines = draft['content'].split('\n')
            title = lines[0].replace('#', '').strip() if lines else "Untitled"
            body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else draft['content']
            
            publish_url = await t_service.create_page(title=title, content_html=body)
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
