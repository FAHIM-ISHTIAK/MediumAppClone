import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.schemas import ArticleListResponse
from app.auth.models import User
from app.authors.schemas import Author, AuthorListResponse, FollowStateResponse, FollowingListResponse
from app.authors.service import (
    follow_author,
    get_author,
    list_author_articles,
    list_authors,
    list_following_entities,
    unfollow_author,
)
from app.common.pagination import PaginationParams
from app.dependencies import ensure_user_access, get_current_user, get_db, get_optional_user


router = APIRouter(tags=["Authors"])


@router.get("/authors", response_model=AuthorListResponse)
async def list_authors_endpoint(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> AuthorListResponse:
    return await list_authors(db, page=pagination.page, limit=pagination.limit, current_user=current_user)


@router.get("/authors/{author_id}", response_model=Author)
async def get_author_endpoint(
    author_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> Author:
    return await get_author(db, author_id=author_id, current_user=current_user)


@router.get("/authors/{author_id}/articles", response_model=ArticleListResponse)
async def list_author_articles_endpoint(
    author_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    return await list_author_articles(db, author_id=author_id, page=pagination.page, limit=pagination.limit)


@router.get("/authors/{author_id}/following/{user_id}", response_model=FollowingListResponse)
async def list_following_endpoint(
    author_id: uuid.UUID,
    user_id: uuid.UUID,
    type: str | None = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowingListResponse:
    ensure_user_access(current_user, user_id)
    await get_author(db, author_id=author_id)
    return await list_following_entities(
        db,
        user_id=user_id,
        follow_type=type,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.post("/authors/{author_id}/follow/{user_id}", response_model=FollowStateResponse)
async def follow_author_endpoint(
    author_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowStateResponse:
    ensure_user_access(current_user, user_id)
    return await follow_author(db, author_id=author_id, user_id=user_id)


@router.delete("/authors/{author_id}/unfollow/{user_id}", response_model=FollowStateResponse)
async def unfollow_author_endpoint(
    author_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowStateResponse:
    ensure_user_access(current_user, user_id)
    return await unfollow_author(db, author_id=author_id, user_id=user_id)
