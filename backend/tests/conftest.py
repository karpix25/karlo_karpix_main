from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    return tmp_path / 'test_vaca.db'


@pytest.fixture(autouse=True)
def isolate_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Prevent tests from reading real credentials/provider settings from local .env.
    monkeypatch.setenv('AUTH_ALLOW_INSECURE_DEV', 'true')
    monkeypatch.setenv('ADMIN_USER_ID', '0')
    monkeypatch.setenv('USERBOT_SECRETS_KEY', 'test-userbot-secret')
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', '')
    monkeypatch.setenv('OPENAI_API_KEY', '')
    monkeypatch.setenv('NINE_ROUTER_API_KEY', '')
    monkeypatch.setenv('OPENROUTER_API_KEY', '')
    monkeypatch.setenv('LLM_PROVIDER', '9router')
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-4.1-mini')
    monkeypatch.setenv('NINE_ROUTER_BASE_URL', 'https://api.9router.com/v1')

    from core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(test_db_path: Path) -> TestClient:
    os.environ['DB_PATH'] = test_db_path.as_posix()
    os.environ['SCHEDULER_ENABLED'] = 'false'
    os.environ['AUTH_ALLOW_INSECURE_DEV'] = 'true'
    os.environ['ADMIN_USER_ID'] = '0'
    os.environ['USERBOT_SECRETS_KEY'] = 'test-userbot-secret'
    os.environ['TELEGRAM_BOT_TOKEN'] = ''

    from core.config import get_settings

    get_settings.cache_clear()

    from main import app

    with TestClient(app) as c:
        yield c

    get_settings.cache_clear()


def auth_headers() -> dict[str, str]:
    return {'X-Telegram-Init-Data': 'user_id=1&username=tester'}
