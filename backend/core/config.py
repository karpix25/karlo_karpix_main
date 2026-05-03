from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.env', '../.env'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    app_name: str = 'VACA Backend'
    environment: str = 'dev'
    db_path: str = './backend/vaca.db'
    default_language: str = 'ru'

    telegram_bot_token: str = ''
    telegram_initdata_max_age_seconds: int = 86400
    auth_allow_insecure_dev: bool = True
    admin_user_id: int = 0
    userbot_secrets_key: str = ''

    # LLM provider selection: 9router | openrouter | openai
    llm_provider: str = '9router'

    # OpenAI-compatible LLM configuration.
    openai_api_key: str = ''
    openai_model: str = 'gpt-4.1-mini'
    openai_base_url: str = 'https://api.9router.com/v1'

    # Explicit aliases for 9router deployments.
    nine_router_api_key: str = ''
    nine_router_base_url: str = 'https://api.9router.com/v1'
    nine_router_model: str = ''
    nine_router_http_referer: str = ''
    nine_router_x_title: str = 'VACA'

    # OpenRouter configuration (OpenAI-compatible).
    openrouter_api_key: str = ''
    openrouter_base_url: str = 'https://openrouter.ai/api/v1'
    openrouter_model: str = 'openai/gpt-4o-mini'
    openrouter_http_referer: str = ''
    openrouter_x_title: str = 'VACA'

    telethon_api_id: int = 0
    telethon_api_hash: str = ''
    telethon_session: str = 'vaca_userbot'

    scheduler_enabled: bool = True
    scheduler_interval_minutes: int = 30

    @property
    def normalized_llm_provider(self) -> str:
        value = (self.llm_provider or '').strip().lower()
        if value in {'openrouter', '9router', 'openai'}:
            return value
        return '9router'

    @property
    def llm_model(self) -> str:
        provider = self.normalized_llm_provider
        if provider == 'openrouter':
            return self.openrouter_model or self.openai_model
        if provider == '9router':
            return self.nine_router_model or self.openai_model
        return self.openai_model

    @property
    def llm_api_key(self) -> str:
        provider = self.normalized_llm_provider
        if provider == 'openrouter':
            return self.openrouter_api_key or self.openai_api_key
        if provider == '9router':
            return self.nine_router_api_key or self.openai_api_key
        return self.openai_api_key

    @property
    def llm_base_url(self) -> str:
        provider = self.normalized_llm_provider
        if provider == 'openrouter':
            return self.openrouter_base_url or self.openai_base_url
        if provider == '9router':
            return self.nine_router_base_url or self.openai_base_url
        return self.openai_base_url

    @property
    def llm_headers(self) -> dict[str, str]:
        provider = self.normalized_llm_provider
        headers: dict[str, str] = {}
        if provider == 'openrouter':
            if self.openrouter_http_referer:
                headers['HTTP-Referer'] = self.openrouter_http_referer
            if self.openrouter_x_title:
                headers['X-Title'] = self.openrouter_x_title
            return headers

        if provider == '9router':
            if self.nine_router_http_referer:
                headers['HTTP-Referer'] = self.nine_router_http_referer
            if self.nine_router_x_title:
                headers['X-Title'] = self.nine_router_x_title
            return headers

        return headers


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
