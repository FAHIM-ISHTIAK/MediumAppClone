import uuid
from datetime import date
from typing import Literal

from pydantic import Field

from app.common.pagination import PaginationMeta
from app.common.schemas import APIModel


HighlightColor = Literal["yellow", "green", "blue", "pink", "purple"]


class HighlightItem(APIModel):
    id: uuid.UUID
    article_id: uuid.UUID
    article_title: str
    text: str
    color: HighlightColor
    date: date
    paragraph_index: int | None = None


class HighlightCreateRequest(APIModel):
    user_id: uuid.UUID
    article_id: uuid.UUID
    text: str = Field(min_length=1)
    color: HighlightColor = "yellow"
    paragraph_index: int | None = Field(default=None, ge=0)


class HighlightListResponse(APIModel):
    data: list[HighlightItem]
    pagination: PaginationMeta
