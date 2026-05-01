from __future__ import annotations

from core.config import get_settings


class AdminNotifier:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def notify_run_status(self, text: str) -> None:
        # MVP: placeholder. In next iteration this can use aiogram bot to deliver ops updates.
        _ = text
