import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.schemas import ArticleListResponse, SaveArticleResponse
from app.auth.models import User
from app.dependencies import ensure_user_access, get_current_user, get_db
from app.highlights.schemas import HighlightListResponse
from app.library.schemas import ReadingAnalyticsResponse, ReadingHistoryListResponse
from app.library.service import (
    delete_history_entry,
    delete_library_highlight,
    delete_library_response,
    get_saved_article_state,
    get_reading_analytics,
    list_library_highlights,
    list_reading_history,
    list_saved_articles,
    list_user_inline_responses,
    list_user_responses,
    unsave_article,
)
from app.responses.schemas import InlineResponseListResponse, ResponseListResponse


router = APIRouter(tags=["Library"])


@router.get("/users/{user_id}/library/highlights", response_model=HighlightListResponse)
async def list_highlights_endpoint(
    user_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HighlightListResponse:
    ensure_user_access(current_user, user_id)
    return await list_library_highlights(db, user_id=user_id, page=page, limit=limit)


@router.delete("/users/{user_id}/library/highlights/{highlight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_highlight_endpoint(
    user_id: uuid.UUID,
    highlight_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ensure_user_access(current_user, user_id)
    await delete_library_highlight(db, user_id=user_id, highlight_id=highlight_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/library/saved", response_model=ArticleListResponse)
async def list_saved_articles_endpoint(
    user_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleListResponse:
    ensure_user_access(current_user, user_id)
    return await list_saved_articles(db, user_id=user_id, page=page, limit=limit)


@router.get("/users/{user_id}/library/saved/{article_id}", response_model=SaveArticleResponse)
async def get_saved_article_state_endpoint(
    user_id: uuid.UUID,
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SaveArticleResponse:
    ensure_user_access(current_user, user_id)
    return await get_saved_article_state(db, user_id=user_id, article_id=article_id)


@router.delete("/users/{user_id}/library/saved/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_article_endpoint(
    user_id: uuid.UUID,
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ensure_user_access(current_user, user_id)
    await unsave_article(db, user_id=user_id, article_id=article_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/library/history", response_model=ReadingHistoryListResponse)
async def list_reading_history_endpoint(
    user_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReadingHistoryListResponse:
    ensure_user_access(current_user, user_id)
    return await list_reading_history(db, user_id=user_id, page=page, limit=limit)


@router.delete("/users/{user_id}/library/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_entry_endpoint(
    user_id: uuid.UUID,
    history_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ensure_user_access(current_user, user_id)
    await delete_history_entry(db, user_id=user_id, history_id=history_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/library/responses", response_model=ResponseListResponse)
async def list_user_responses_endpoint(
    user_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseListResponse:
    ensure_user_access(current_user, user_id)
    return await list_user_responses(db, user_id=user_id, page=page, limit=limit)


@router.delete("/users/{user_id}/library/responses/{article_id}/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_response_endpoint(
    user_id: uuid.UUID,
    article_id: uuid.UUID,
    response_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ensure_user_access(current_user, user_id)
    await delete_library_response(db, user_id=user_id, article_id=article_id, response_id=response_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/library/history/analytics", response_model=ReadingAnalyticsResponse)
async def get_reading_analytics_endpoint(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReadingAnalyticsResponse:
    ensure_user_access(current_user, user_id)
    return await get_reading_analytics(db, user_id=user_id)


@router.get("/users/{user_id}/library/inline-responses", response_model=InlineResponseListResponse)
async def list_user_inline_responses_endpoint(
    user_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InlineResponseListResponse:
    ensure_user_access(current_user, user_id)
    return await list_user_inline_responses(db, user_id=user_id, page=page, limit=limit)
