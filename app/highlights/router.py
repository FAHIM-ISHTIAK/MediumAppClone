import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.common.exceptions import forbidden
from app.dependencies import ensure_user_access, get_current_user, get_db
from app.highlights.schemas import HighlightCreateRequest, HighlightItem, HighlightListResponse
from app.highlights.service import create_highlight, delete_highlight, list_article_highlights


router = APIRouter(tags=["Highlights"])


@router.get("/articles/{article_id}/highlights/{user_id}", response_model=HighlightListResponse)
async def list_article_highlights_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HighlightListResponse:
    ensure_user_access(current_user, user_id)
    return await list_article_highlights(db, article_id=article_id, user_id=user_id)


@router.post(
    "/articles/{article_id}/highlight/{user_id}",
    response_model=HighlightItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_article_highlight_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: HighlightCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HighlightItem:
    ensure_user_access(current_user, user_id)
    if payload.user_id != user_id or payload.article_id != article_id:
        raise forbidden("Path parameters do not match the request body.")
    return await create_highlight(
        db,
        article_id=article_id,
        user_id=user_id,
        text=payload.text,
        color=payload.color,
        paragraph_index=payload.paragraph_index,
    )


@router.delete("/articles/{article_id}/highlights/{user_id}/{highlight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article_highlight_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    highlight_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ensure_user_access(current_user, user_id)
    await delete_highlight(db, article_id=article_id, user_id=user_id, highlight_id=highlight_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
