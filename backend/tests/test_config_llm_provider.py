from __future__ import annotations

from core.config import get_settings


def test_openrouter_resolution(monkeypatch) -> None:
    monkeypatch.setenv('LLM_PROVIDER', 'openrouter')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'or-key')
    monkeypatch.setenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    monkeypatch.setenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini')
    monkeypatch.setenv('OPENROUTER_HTTP_REFERER', 'https://example.com')
    monkeypatch.setenv('OPENROUTER_X_TITLE', 'VACA')

    get_settings.cache_clear()
    s = get_settings()

    assert s.normalized_llm_provider == 'openrouter'
    assert s.llm_api_key == 'or-key'
    assert s.llm_base_url == 'https://openrouter.ai/api/v1'
    assert s.llm_model == 'openai/gpt-4o-mini'
    assert s.llm_headers['HTTP-Referer'] == 'https://example.com'
    assert s.llm_headers['X-Title'] == 'VACA'


def test_ninerouter_fallback_to_openai_key(monkeypatch) -> None:
    monkeypatch.setenv('LLM_PROVIDER', '9router')
    monkeypatch.setenv('NINE_ROUTER_API_KEY', '')
    monkeypatch.setenv('OPENAI_API_KEY', 'shared-key')
    monkeypatch.setenv('NINE_ROUTER_BASE_URL', 'https://router.karpix.com/v1')

    get_settings.cache_clear()
    s = get_settings()

    assert s.normalized_llm_provider == '9router'
    assert s.llm_api_key == 'shared-key'
    assert s.llm_base_url == 'https://router.karpix.com/v1'
