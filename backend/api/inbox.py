from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.deps import require_user
from schemas import InboxItem
from core.repository import list_inbox

router = APIRouter(prefix='/api/inbox', tags=['inbox'])


@router.get('', response_model=list[InboxItem])
async def get_inbox(
    status: str | None = Query(default=None),
    _user=Depends(require_user),
) -> list[InboxItem]:
    rows = await list_inbox(status=status)
    return [InboxItem(**row) for row in rows]
