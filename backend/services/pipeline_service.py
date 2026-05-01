from __future__ import annotations

from pathlib import Path

from agents.content_orchestrator import ContentOrchestratorAgent
from core.models import CandidateStatus, DraftPlatform, DraftStatus, RunStatus
from core.repository import (
    RawMessageInput,
    create_candidate,
    create_draft,
    create_pipeline_run,
    finish_pipeline_run,
    get_setting,
    insert_raw_message,
    set_draft_status,
)
from services.rule_engine import SpamRuleEngine
from services.telethon_service import TelethonUserbotService


class PipelineService:
    def __init__(self) -> None:
        self.userbot = TelethonUserbotService()
        self.agent = ContentOrchestratorAgent()
        self.rules = SpamRuleEngine(Path('./backend/memory/sorting_rules.md'))

    async def run(self, trigger_source: str = 'manual') -> dict:
        run_id = await create_pipeline_run(trigger_source=trigger_source)
        ingested_count = 0
        candidates_count = 0
        drafts_count = 0

        try:
            source_settings = await get_setting('sources')
            skill_settings = await get_setting('skills')
            channels = source_settings.get('channels', [])

            messages = await self.userbot.fetch_new_messages(channels)

            for message in messages:
                raw_id = await insert_raw_message(
                    RawMessageInput(
                        channel_username=message.channel_username,
                        message_id=message.message_id,
                        text=message.text,
                        posted_at=message.posted_at,
                    )
                )
                if not raw_id:
                    continue

                ingested_count += 1
                summary = await self.agent.summarize(message.text)
                evaluation = self.rules.evaluate(message.text, skill_settings)

                candidate_status = CandidateStatus.accepted if evaluation.accepted else CandidateStatus.rejected
                candidate_id = await create_candidate(
                    raw_message_id=raw_id,
                    summary=summary,
                    relevance_score=evaluation.relevance_score,
                    status=candidate_status.value,
                    reason=evaluation.reason,
                )
                candidates_count += 1

                if candidate_status == CandidateStatus.rejected:
                    continue

                for platform in (DraftPlatform.telegram, DraftPlatform.threads):
                    generated = await self.agent.generate_draft(
                        platform=platform.value,
                        summary=summary,
                        source_text=message.text,
                    )
                    valid, error = await self.agent.self_check(generated.content)
                    status = DraftStatus.in_review if valid else DraftStatus.error
                    draft_id = await create_draft(
                        candidate_id=candidate_id,
                        platform=platform,
                        content=generated.content,
                        cta=generated.cta,
                        hashtags=generated.hashtags,
                        status=status,
                    )
                    drafts_count += 1
                    if not valid and error:
                        await set_draft_status(draft_id, DraftStatus.error, error=error)

            await finish_pipeline_run(
                run_id,
                status=RunStatus.completed,
                ingested_count=ingested_count,
                candidates_count=candidates_count,
                drafts_count=drafts_count,
            )
            return {
                'run_id': run_id,
                'status': RunStatus.completed.value,
                'ingested_count': ingested_count,
                'candidates_count': candidates_count,
                'drafts_count': drafts_count,
            }
        except Exception as exc:
            await finish_pipeline_run(
                run_id,
                status=RunStatus.failed,
                ingested_count=ingested_count,
                candidates_count=candidates_count,
                drafts_count=drafts_count,
                error=str(exc),
            )
            raise
