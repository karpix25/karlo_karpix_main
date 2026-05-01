from __future__ import annotations

import pytest

from agents.content_orchestrator import ContentOrchestratorAgent


@pytest.mark.asyncio
async def test_orchestrator_generates_fallback_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('OPENAI_API_KEY', '')
    monkeypatch.setenv('NINE_ROUTER_API_KEY', '')
    monkeypatch.setenv('OPENROUTER_API_KEY', '')
    monkeypatch.setenv('LLM_PROVIDER', 'openrouter')

    from core.config import get_settings

    get_settings.cache_clear()
    agent = ContentOrchestratorAgent()
    draft = await agent.generate_draft('telegram', 'Короткое резюме', 'Технический исходник')

    assert draft.platform == 'telegram'
    assert len(draft.content) > 10
    ok, error = await agent.self_check(draft.content)
    assert ok is True
    assert error is None
