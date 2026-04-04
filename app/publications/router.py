import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.schemas import ArticleListResponse
from app.auth.models import User
from app.authors.schemas import FollowingListResponse
from app.authors.service import list_following_entities
from app.common.pagination import PaginationParams
from app.dependencies import ensure_user_access, get_current_user, get_db
from app.publications.schemas import FollowPublicationResponse, Publication, PublicationListResponse
from app.publications.service import (
    follow_publication,
    get_publication,
    list_publication_articles,
    list_publications,
    unfollow_publication,
)


router = APIRouter(tags=["Publications"])


@router.get("/publications", response_model=PublicationListResponse)
async def list_publications_endpoint(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PublicationListResponse:
    return await list_publications(db, page=pagination.page, limit=pagination.limit)


@router.get("/publications/{publication_id}", response_model=Publication)
async def get_publication_endpoint(
    publication_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Publication:
    return await get_publication(db, publication_id=publication_id)


@router.get("/publications/{publication_id}/articles", response_model=ArticleListResponse)
async def list_publication_articles_endpoint(
    publication_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    return await list_publication_articles(
        db,
        publication_id=publication_id,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get("/publications/{publication_id}/following/{user_id}", response_model=FollowingListResponse)
async def list_publication_following_endpoint(
    publication_id: uuid.UUID,
    user_id: uuid.UUID,
    type: str | None = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowingListResponse:
    ensure_user_access(current_user, user_id)
    await get_publication(db, publication_id=publication_id)
    return await list_following_entities(
        db,
        user_id=user_id,
        follow_type=type,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.post("/publications/{publication_id}/follow/{user_id}", response_model=FollowPublicationResponse)
async def follow_publication_endpoint(
    publication_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowPublicationResponse:
    ensure_user_access(current_user, user_id)
    return await follow_publication(db, publication_id=publication_id, user_id=user_id)


@router.delete("/publications/{publication_id}/unfollow/{user_id}", response_model=FollowPublicationResponse)
async def unfollow_publication_endpoint(
    publication_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowPublicationResponse:
    ensure_user_access(current_user, user_id)
    return await unfollow_publication(db, publication_id=publication_id, user_id=user_id)
