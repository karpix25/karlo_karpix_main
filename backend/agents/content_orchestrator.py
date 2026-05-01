from __future__ import annotations

from dataclasses import dataclass

from services.llm_client import LLMClient


@dataclass
class GeneratedDraft:
    platform: str
    content: str
    cta: str
    hashtags: str


class ContentOrchestratorAgent:
    def __init__(self) -> None:
        self.llm = LLMClient()

    async def summarize(self, text: str) -> str:
        if not self.llm.enabled:
            return text[:180].strip()

        prompt = f'Сделай сжатое резюме поста для контент-менеджера личного бренда: {text}'
        return await self.llm.complete(prompt)

    async def generate_draft(self, platform: str, summary: str, source_text: str) -> GeneratedDraft:
        if not self.llm.enabled:
            if platform == 'telegram':
                content = f"{summary}\n\nКлючевая мысль: {source_text[:120]}..."
            else:
                content = f"{summary}\n\nТред-версия: {source_text[:100]}..."
            return GeneratedDraft(
                platform=platform,
                content=content,
                cta='Напиши в личку, если хочешь разобрать это для своего проекта.',
                hashtags='#личныйбренд #архитектура #ai',
            )

        prompt = (
            'Сгенерируй пост под личный бренд Carlo на русском языке. '
            f'Платформа: {platform}. '\
            f'Резюме источника: {summary}. '\
            f'Исходный текст: {source_text}. '\
            'Требования: без воды, практично, tone-of-voice архитектора и предпринимателя, '
            'добавь отдельные блоки CTA и hashtags.'
        )
        generated = await self.llm.complete(prompt)
        content = generated
        cta = 'Если нужен разбор под ваш продукт, напишите мне.'
        hashtags = '#ai #product #softwarearchitecture'
        return GeneratedDraft(platform=platform, content=content, cta=cta, hashtags=hashtags)

    async def self_check(self, content: str) -> tuple[bool, str | None]:
        if len(content.strip()) < 30:
            return False, 'content_too_short'
        return True, None
