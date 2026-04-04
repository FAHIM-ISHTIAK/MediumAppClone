import uuid
from datetime import date
from typing import Optional

from pydantic import Field

from app.articles.schemas import ArticleAuthor
from app.common.pagination import PaginationMeta
from app.common.schemas import APIModel


class ResponseItem(APIModel):
    id: uuid.UUID
    article_id: uuid.UUID
    article_title: str
    text: str
    date: date
    likes: int
    author: ArticleAuthor
    parent_id: Optional[uuid.UUID] = None
    reply_count: int = 0
    is_edited: bool = False


class ResponseListResponse(APIModel):
    data: list[ResponseItem]
    pagination: PaginationMeta
    total_response_count: int = 0


class ResponseClapResponse(APIModel):
    likes: int


class ResponseClapRequest(APIModel):
    user_id: uuid.UUID
    count: int = Field(default=1, ge=1, le=50)


class ResponseCreateRequest(APIModel):
    user_id: uuid.UUID
    text: str = Field(min_length=1, max_length=5000)


class ResponseUpdateRequest(APIModel):
    user_id: uuid.UUID
    text: str = Field(min_length=1, max_length=5000)


class ReplyCreateRequest(APIModel):
    user_id: uuid.UUID
    text: str = Field(min_length=1, max_length=5000)


class InlineResponseItem(APIModel):
    id: uuid.UUID
    article_id: uuid.UUID
    user_id: uuid.UUID
    selected_text: str
    paragraph_index: int
    text: str
    date: date
    likes: int


class InlineResponseCreateRequest(APIModel):
    user_id: uuid.UUID
    selected_text: str
    paragraph_index: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=2000)


class InlineResponseUpdateRequest(APIModel):
    user_id: uuid.UUID
    text: str = Field(min_length=1, max_length=2000)


class InlineResponseListResponse(APIModel):
    data: list[InlineResponseItem]
    pagination: PaginationMeta
