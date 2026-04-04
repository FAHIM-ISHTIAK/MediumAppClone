from dataclasses import dataclass
from math import ceil

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import APIModel


class PaginationMeta(APIModel):
    page: int
    limit: int
    total_items: int
    total_pages: int


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1)
    limit: int = Query(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


async def paginate_scalars(
    db: AsyncSession,
    stmt: Select,
    page: int,
    limit: int,
):
    total = await db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    result = await db.scalars(stmt.offset((page - 1) * limit).limit(limit))
    items = result.all()
    total_items = total or 0
    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=ceil(total_items / limit) if total_items else 0,
    )
    return items, pagination
