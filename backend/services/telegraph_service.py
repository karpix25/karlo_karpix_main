from __future__ import annotations
import httpx
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

class TelegraphService:
    BASE_URL = "https://api.telegra.ph"

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token

    async def create_page(self, title: str, content_html: str, author_name: str = "VACA Agent") -> str:
        """
        Creates a page on Telegra.ph.
        Note: Telegra.ph content must be in its own Node format, 
        but for simplicity we can use a very basic converter or just raw text nodes.
        Better yet: We can use their helper if we had one, but we'll manually wrap in a <p> tag style.
        """
        if not self.access_token:
            # Create a temporary account if no token
            await self._create_account(author_name)

        # Basic HTML to Node conversion (very simplified)
        # Telegra.ph expects a JSON array of objects like {"tag": "p", "children": ["text"]}
        nodes = self._html_to_nodes(content_html)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/createPage",
                data={
                    "access_token": self.access_token,
                    "title": title,
                    "author_name": author_name,
                    "content": json.dumps(nodes),
                    "return_content": "true"
                }
            )
            data = resp.json()
            if not data.get("ok"):
                raise Exception(f"Telegra.ph error: {data.get('error')}")
            
            return data["result"]["url"]

    async def _create_account(self, short_name: str):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/createAccount",
                params={"short_name": short_name, "author_name": short_name}
            )
            data = resp.json()
            if data.get("ok"):
                self.access_token = data["result"]["access_token"]
                logger.info(f"Created new Telegra.ph account: {self.access_token}")

    def _html_to_nodes(self, html: str) -> list[dict]:
        # Very simple: split by double newlines and wrap in <p>
        paragraphs = [p.strip() for p in html.split('\n\n') if p.strip()]
        return [{"tag": "p", "children": [p]} for p in paragraphs]
