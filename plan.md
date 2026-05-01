# Project: Vibetraffic Autonomous Content Agent (VACA)
# Role: Senior Full-Stack AI Engineer

## 🎯 Project Objective
Build an autonomous content engine (LLM OS paradigm) for Carlo, a software architect and entrepreneur. 
The system ingests posts from Telegram channels, filters spam, generates multi-platform content (Telegram, Telegraph, Threads, IG Reels) adapting to Carlo's Tone of Voice, and is managed via a React-based Telegram Mini App (TMA).
**Strict Rule:** No no-code tools (like n8n) are allowed. 100% pure code.

## 🛠 Tech Stack
**Backend:**
- Python 3.11+, `asyncio`
- Frameworks: `FastAPI` (API), `Pydantic AI` (Agent Orchestration)
- LLM Gateway: `openai` client routing to `9router` (base_url: https://api.9router.com/v1)
- Data/State: `SQLite` (async, e.g., `aiosqlite`)
- Integrations: `Telethon` (Userbot scraper), `aiogram 3.x` (Admin notifications), `python-telegraph`.

**Frontend (Mini App / TMA):**
- React 18+, Vite, TypeScript
- UI: `Tailwind CSS`, `Shadcn UI` (or Radix primitives)
- Editor: `Tiptap` (Headless rich-text editor)
- TG Integration: `@twa-dev/sdk`

## 📂 Monorepo Structure
```text
/
├── backend/
│   ├── agents/             # Pydantic AI definitions (Planner, Writer, Reflector)
│   ├── memory/             # Compiled Memory (.md files)
│   │   ├── identity.md     # Carlo's identity and core tone
│   │   ├── sorting_rules.md# Rules for spam filtering
│   │   ├── offers.md       # CTA links (SEO Catalog, LMS Skola, B2B)
│   │   └── skills/         # Toggleable marketing frameworks (PAS, Hormozi, etc.)
│   ├── tools/              # Tools for Pydantic AI (web_search, etc.)
│   ├── core/               # Database models (SQLite), Config, Pydantic schemas
│   ├── api/                # FastAPI routers (endpoints for React frontend)
│   └── services/           # Telethon scraper logic & Aiogram bot logic
├── frontend/
│   ├── src/
│   │   ├── components/     # UI, Tiptap Editor, Skill Toggles
│   │   ├── pages/          # Dashboard (Inbox), Draft Review (Tabs), Auth Settings
│   │   └── lib/            # API clients (Axios/Fetch) interfacing with FastAPI
├── .env.example
└── docker-compose.yml      # FastAPI, React build serve, SQLite volume


Core Architecture Mechanics
Compiled Memory (Karpathy Method):

The agent's "brain" is the /memory folder.

Before agent.run(), read identity.md and any active skills/*.md (passed via React settings) to build the dynamic system prompt.

Data Flow (Triple Play):

Pydantic AI must output a structured JSON matching this schema for approved posts:
{ category: str, tg_post: str | null, telegraph_html: str | null, threads_text: str | null, insta_reels_script: dict | null, selected_offer: str }

Feedback Loop (Reject & Learn):

If the user clicks "Reject & Learn" in the React TMA and provides a reason, trigger the Reflector Agent.

Reflector Agent takes the reason and the original post, and rewrites sorting_rules.md or identity.md locally to prevent future mistakes.

Telethon Auth Flow:

The React TMA must have an "Account/Settings" page to handle Telethon Userbot auth (Phone -> Code -> 2FA Password).

FastAPI handles the Telethon auth states and saves the .session file securely. Do not hardcode phone numbers.

🚀 Execution Plan (Phases)
Agent: Complete these phases sequentially. Do not move to the next phase until the current one is fully implemented and tested.

Phase 1: Foundation & Memory
Initialize project structure (Backend + Frontend).

Setup docker-compose.yml for local development.

Create all .md files in /backend/memory/ with basic placeholder instructions (e.g., identity.md: "I am Carlo, tech entrepreneur. Write concisely, no AI fluff.").

Setup SQLite database with tables: posts (id, source, raw_text, status) and drafts (JSON payload of generated content).

Phase 2: Backend Brain (Pydantic AI & API)
Implement Pydantic AI agents using 9router.

Create PlannerAgent (evaluates raw post -> decides platforms).

Create WriterAgent (generates the multi-platform JSON based on memory + skills).

Create ReflectorAgent (handles the Reject & Learn loop, rewrites .md files).

Build FastAPI endpoints: /drafts (GET/POST), /memory/skills (GET/POST to toggle active skills), /reject (POST trigger for Reflector).

Phase 3: Telethon Scraper & Aiogram
Implement Telethon client. Build the FastAPI endpoints for Phone/Code/2FA auth so the frontend can drive the login process.

Implement the scraping loop (saving new posts to SQLite).

Implement Aiogram bot to send a notification to the admin ID: "New draft ready. [Open Mini App]".

Implement python-telegraph function to publish HTML payloads.

Phase 4: Frontend TMA (React)
Initialize Vite + React. Install @twa-dev/sdk.

Build Tabbed Interface for Draft Review: TG Post | Telegraph | Threads | Reels Script.

Integrate Tiptap for the Telegraph HTML editing tab.

Build the "Skills Management" view (toggles that fetch/update the backend configuration).

Build the "Reject & Learn" modal.

Build the "Userbot Auth" screen.

💻 Coding Guidelines
Write clean, modular, async Python code.

Always use try/except blocks for external API calls (Telethon, LLM, Telegraph).

Use proper logging (logger.info, logger.error).

For the frontend, ensure it's mobile-first, mimicking native iOS/Telegram aesthetics.