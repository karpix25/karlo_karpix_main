from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import get_settings
from core.repository import get_setting
from services.pipeline_service import PipelineService


class PipelineScheduler:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.pipeline = PipelineService()

    async def start(self) -> None:
        if not self.settings.scheduler_enabled:
            return

        await self.reload_from_settings()
        if not self.scheduler.running:
            self.scheduler.start()

    async def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def reload_from_settings(self) -> None:
        schedule = await get_setting('schedule')
        interval = int(schedule.get('interval_minutes', self.settings.scheduler_interval_minutes))
        if self.scheduler.get_job('vaca_pipeline'):
            self.scheduler.remove_job('vaca_pipeline')
        self.scheduler.add_job(self._run_scheduled, 'interval', minutes=max(interval, 1), id='vaca_pipeline')

    async def _run_scheduled(self) -> None:
        await self.pipeline.run(trigger_source='scheduler')
