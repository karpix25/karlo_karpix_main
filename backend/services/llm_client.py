from __future__ import annotations

from openai import AsyncOpenAI

from core.config import get_settings


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.llm_model
        api_key = settings.llm_api_key
        self.enabled = bool(api_key)

        self.client = AsyncOpenAI(
            api_key=api_key or 'disabled',
            base_url=settings.llm_base_url,
            default_headers=settings.llm_headers or None,
        )

    async def complete(self, prompt: str, system: str = '') -> str:
        if not self.enabled:
            return 'LLM disabled. Fallback generation used.'

        response = await self.client.responses.create(
            model=self.model,
            input=[
                {'role': 'system', 'content': system or 'You are a senior content strategist.'},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.4,
        )
        return response.output_text.strip()
