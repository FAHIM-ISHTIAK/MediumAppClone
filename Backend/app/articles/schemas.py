import uuid
from datetime import date

from pydantic import Field, field_validator

from app.common.pagination import PaginationMeta
from app.common.schemas import APIModel


class ArticleAuthor(APIModel):
    id: uuid.UUID
    name: str
    avatar: str | None = None
    bio: str | None = None


class ArticleSummary(APIModel):
    id: uuid.UUID
    title: str
    subtitle: str | None = None
    author: ArticleAuthor
    publication: str | None = None
    reading_time: int
    tags: list[str]
    claps: int
    date: date
    cover_image: str | None = None


class Article(APIModel):
    id: uuid.UUID
    title: str
    subtitle: str | None = None
    author: ArticleAuthor
    publication: str | None = None
    reading_time: int
    tags: list[str]
    claps: int
    date: date
    content: list[str]
    cover_image: str | None = None


class ArticleListResponse(APIModel):
    data: list[ArticleSummary]
    pagination: PaginationMeta


class ClapArticleRequest(APIModel):
    user_id: uuid.UUID
    count: int = Field(default=1, ge=1, le=50)


class ClapArticleResponse(APIModel):
    total_claps: int


class TrackReadingRequest(APIModel):
    time_spent: int = Field(ge=0)
    read_percentage: int = Field(default=0, ge=0, le=100)


class SaveArticleResponse(APIModel):
    saved: bool
    article_id: uuid.UUID


class SortOption(str):
    pass


def _normalize_text(paragraph: str) -> str:
    return " ".join(paragraph.split())


class BaseArticlePayload(APIModel):
    @field_validator("*", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class ArticleCreateRequest(BaseArticlePayload):
    user_id: uuid.UUID
    title: str = Field(max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    publication_id: uuid.UUID | None = None
    tags: list[str] = Field(default_factory=list, max_length=5)
    content: list[str]
    cover_image: str | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: list[str]) -> list[str]:
        cleaned = [_normalize_text(part) for part in value if _normalize_text(part)]
        if not cleaned:
            raise ValueError("Article content cannot be empty.")
        return cleaned
