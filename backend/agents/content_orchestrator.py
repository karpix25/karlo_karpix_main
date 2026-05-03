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

        prompt = f"""
        Проанализируй пост из Telegram и подготовь его для ленты.
        
        Формат ответа (строго):
        1. Первая строка: Мощный заголовок темы (Hook).
        2. Вторая строка: пустая.
        3. Остальное: Краткое описание сути и пользы (2-3 предложения).
        
        Правила:
        - КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать слова "Хук", "Hook", "Заголовок", "Суть", "Тема", "Essence" или "Описание".
        - Пиши сразу по делу, без вводных фраз.
        - НЕ используй списки и нумерацию.
        
        Текст поста:
        {text}
        """
        return await self.llm.complete(prompt)

    async def generate_draft(self, platform: str, summary: str, source_text: str) -> GeneratedDraft:
        if not self.llm.enabled:
            content = f"[{platform}] {summary}"
            return GeneratedDraft(platform=platform, content=content, cta='Contact me.', hashtags='#ai')

        platform_prompt = ""
        if platform == '5s Reels':
            platform_prompt = 'Формат: Короткий 5-секундный Reels. Напиши 1 цепляющий заголовок для видео и краткий текст для описания.'
        elif platform == 'Аватар':
            platform_prompt = 'Формат: Скрипт для говорящего AI-аватара на 20 секунд.'
        elif platform == 'Карусель':
            platform_prompt = 'Формат: Текст для карточек карусели (3-5 слайдов).'
        elif platform == 'Telegra.ph':
            platform_prompt = 'Формат: Развернутый лонгрид для Telegra.ph с заголовком и структурированным текстом.'
        else:
            platform_prompt = f'Платформа: {platform}.'

        prompt = (
            'Сгенерируй контент под личный бренд на русском языке. '
            f'{platform_prompt} '
            f'Резюме: {summary}. '
            f'Исходный текст: {source_text}. '
            'Тон: экспертный, без воды.'
        )
        content = await self.llm.complete(prompt)
        return GeneratedDraft(platform=platform, content=content, cta='Обсудить в ЛС.', hashtags='#ai #tech')

    async def generate_digest(self, items: list[dict[str, Any]]) -> GeneratedDraft:
        if not self.llm.enabled:
            content = "Дайджест новостей:\n" + "\n".join([f"- {i['summary'][:50]}" for i in items])
            return GeneratedDraft(platform='Дайджест', content=content, cta='', hashtags='')

        summaries = "\n".join([f"- {i['summary']}" for i in items])
        prompt = f"""
        Создай итоговый дайджест новостей на основе следующих материалов:
        {summaries}
        
        Требования:
        1. Сгруппируй новости по темам.
        2. Напиши краткое интро.
        3. Для каждой новости сделай ёмкий буллит.
        4. Стиль: профессиональный, сдержанный.
        """
        content = await self.llm.complete(prompt)
        return GeneratedDraft(platform='Дайджест', content=content, cta='Подписывайтесь на обновления.', hashtags='#digest #ai')

    async def self_check(self, content: str) -> tuple[bool, str | None]:
        if len(content.strip()) < 30:
            return False, 'content_too_short'
        return True, None
