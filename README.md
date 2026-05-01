# VACA MVP

Monorepo with:
- `backend/`: FastAPI + SQLite + scheduler + content orchestration.
- `frontend/`: React Telegram Mini App for inbox, draft review, settings.

## Quick Start

1. Copy env:
```bash
cp .env.example .env
```
2. Run backend locally:
```bash
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload
```
3. Run frontend locally:
```bash
cd frontend
npm install
npm run dev
```

## Deploy With Docker Compose (VPS / Coolify)

This repository includes production-oriented Dockerfiles and compose setup.

1. Set environment values in `.env` (at minimum auth/admin/security keys).
2. Deploy with compose:
```bash
docker compose up -d --build
```
3. Expose `frontend` service via your reverse proxy/domain.  
Frontend serves the app and proxies `/api/*` to backend internally.

## LLM Providers (OpenRouter / 9router / OpenAI)

### OpenRouter (recommended)

```bash
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Optional provider headers:

```bash
OPENROUTER_HTTP_REFERER=https://your-domain.example
OPENROUTER_X_TITLE=VACA
```

### 9router

```bash
LLM_PROVIDER=9router
NINE_ROUTER_API_KEY=your_9router_key
NINE_ROUTER_BASE_URL=https://router.karpix.com/v1
# optional:
NINE_ROUTER_MODEL=gpt-5.4
```

### Direct OpenAI

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

After setting env, run `POST /api/runs/trigger` and drafts will be generated via the selected provider.

## API Auth

All private endpoints require `X-Telegram-Init-Data` header.
In local dev (`AUTH_ALLOW_INSECURE_DEV=true` and empty `TELEGRAM_BOT_TOKEN`) header may contain simple query-string, e.g. `user_id=1&username=dev`.

## Implemented Endpoints

- `POST /api/runs/trigger`
- `GET /api/inbox?status=`
- `GET /api/drafts?platform=&status=`
- `GET /api/drafts/{id}`
- `PUT /api/drafts/{id}`
- `POST /api/drafts/{id}/approve`
- `POST /api/drafts/{id}/reject`
- `POST /api/drafts/{id}/regenerate`
- `GET/PUT /api/settings/sources`
- `GET/PUT /api/settings/schedule`
- `GET/PUT /api/settings/skills`
- `GET /api/settings/memory`
