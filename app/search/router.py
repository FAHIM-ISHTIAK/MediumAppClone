from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams
from app.dependencies import get_db
from app.search.schemas import SearchResponse
from app.search.service import search


router = APIRouter(tags=["Search"])


@router.get("/search", response_model=SearchResponse)
async def search_endpoint(
    q: str = Query(min_length=1),
    type: str | None = Query(default=None, pattern="^(stories|people|publications)$"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    return await search(db, q=q, type_=type, page=pagination.page, limit=pagination.limit)
