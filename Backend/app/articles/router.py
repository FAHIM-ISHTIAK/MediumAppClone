import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.schemas import (
    Article,
    ArticleListResponse,
    ClapArticleRequest,
    ClapArticleResponse,
    SaveArticleResponse,
    TrackReadingRequest,
)
from app.articles.service import (
    clap_article,
    get_article,
    list_articles,
    save_article,
    track_article_reading,
)
from app.auth.models import User
from app.common.exceptions import forbidden
from app.common.pagination import PaginationParams
from app.dependencies import ensure_user_access, get_current_user, get_db, get_optional_user


router = APIRouter(tags=["Articles"])


@router.get("/user/{user_id}/articles", response_model=ArticleListResponse)
async def list_articles_endpoint(
    user_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    tag: str | None = Query(default=None),
    sort: str = Query(default="recommended", pattern="^(latest|popular|recommended)$"),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    return await list_articles(db, tag=tag, sort=sort, page=pagination.page, limit=pagination.limit)


@router.get("/articles/{article_id}", response_model=Article)
async def get_article_endpoint(
    article_id: uuid.UUID,
    time_spent: int | None = Query(default=None, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> Article:
    return await get_article(
        db,
        article_id=article_id,
        user_id=current_user.id if current_user else None,
        time_spent=time_spent,
    )


@router.post("/articles/{article_id}/clap/{user_id}", response_model=ClapArticleResponse)
async def clap_article_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: ClapArticleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClapArticleResponse:
    ensure_user_access(current_user, user_id)
    if payload.user_id != user_id:
        raise forbidden("Path user does not match body user.")
    return await clap_article(db, article_id=article_id, user_id=user_id, count=payload.count)


@router.post("/articles/{article_id}/track")
async def track_article_endpoint(
    article_id: uuid.UUID,
    payload: TrackReadingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    return await track_article_reading(
        db,
        article_id=article_id,
        user_id=current_user.id,
        time_spent=payload.time_spent,
        read_percentage=payload.read_percentage,
    )


@router.post(
    "/users/{user_id}/library/saved/{article_id}",
    response_model=SaveArticleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_article_endpoint(
    user_id: uuid.UUID,
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SaveArticleResponse:
    ensure_user_access(current_user, user_id)
    return await save_article(db, article_id=article_id, user_id=user_id)
