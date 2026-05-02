from __future__ import annotations

import asyncio

# Single process-wide lock to prevent concurrent writes into the same
# Telethon SQLite session file.
telethon_session_lock = asyncio.Lock()
