import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.common.exceptions import forbidden
from app.common.pagination import PaginationParams
from app.dependencies import ensure_user_access, get_current_user, get_optional_user, get_db
from app.responses.schemas import (
    ResponseClapRequest,
    InlineResponseCreateRequest,
    InlineResponseItem,
    InlineResponseListResponse,
    InlineResponseUpdateRequest,
    ResponseClapResponse,
    ResponseCreateRequest,
    ResponseItem,
    ResponseListResponse,
    ResponseUpdateRequest,
)
from app.responses.service import (
    clap_response,
    create_inline_response,
    create_response,
    delete_inline_response,
    delete_response,
    list_inline_responses,
    list_responses,
    update_inline_response,
    update_response,
)


router = APIRouter(tags=["Responses"])


@router.get("/articles/{article_id}/responses", response_model=ResponseListResponse)
async def list_article_responses_endpoint(
    article_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ResponseListResponse:
    return await list_responses(db, article_id=article_id, page=pagination.page, limit=pagination.limit)


@router.post(
    "/articles/{article_id}/responses/{user_id}",
    response_model=ResponseItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_article_response_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: ResponseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseItem:
    ensure_user_access(current_user, user_id)
    if payload.user_id != user_id:
        raise forbidden("Path user does not match body user.")
    return await create_response(db, article_id=article_id, user_id=user_id, text=payload.text)


@router.put("/articles/{article_id}/responses/{user_id}/{response_id}", response_model=ResponseItem)
async def update_article_response_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    response_id: uuid.UUID,
    payload: ResponseUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseItem:
    ensure_user_access(current_user, user_id)
    if payload.user_id != user_id:
        raise forbidden("Path user does not match body user.")
    return await update_response(
        db,
        article_id=article_id,
        user_id=user_id,
        response_id=response_id,
        text=payload.text,
    )


@router.delete("/articles/{article_id}/responses/{user_id}/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article_response_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    response_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ensure_user_access(current_user, user_id)
    await delete_response(db, article_id=article_id, user_id=user_id, response_id=response_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/articles/{article_id}/responses/{response_id}/clap/{user_id}", response_model=ResponseClapResponse)
async def clap_article_response_endpoint(
    article_id: uuid.UUID,
    response_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: ResponseClapRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseClapResponse:
    ensure_user_access(current_user, user_id)
    if payload.user_id != user_id:
        raise forbidden("Path user does not match body user.")
    likes = await clap_response(
        db,
        article_id=article_id,
        response_id=response_id,
        count=payload.count,
    )
    return ResponseClapResponse(likes=likes)


@router.get("/articles/{article_id}/inline-responses", response_model=InlineResponseListResponse)
async def list_inline_responses_endpoint(
    article_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> InlineResponseListResponse:
    return await list_inline_responses(
        db,
        article_id=article_id,
        user_id=current_user.id if current_user else None,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.post(
    "/articles/{article_id}/inline-responses/{user_id}",
    response_model=InlineResponseItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_inline_response_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: InlineResponseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InlineResponseItem:
    ensure_user_access(current_user, user_id)
    if payload.user_id != user_id:
        raise forbidden("Path user does not match body user.")
    return await create_inline_response(
        db,
        article_id=article_id,
        user_id=user_id,
        selected_text=payload.selected_text,
        paragraph_index=payload.paragraph_index,
        text=payload.text,
    )


@router.put(
    "/articles/{article_id}/inline-responses/{user_id}/{inline_response_id}",
    response_model=InlineResponseItem,
)
async def update_inline_response_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    inline_response_id: uuid.UUID,
    payload: InlineResponseUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InlineResponseItem:
    ensure_user_access(current_user, user_id)
    if payload.user_id != user_id:
        raise forbidden("Path user does not match body user.")
    return await update_inline_response(
        db,
        article_id=article_id,
        user_id=user_id,
        inline_response_id=inline_response_id,
        text=payload.text,
    )


@router.delete(
    "/articles/{article_id}/inline-responses/{user_id}/{inline_response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_inline_response_endpoint(
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    inline_response_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ensure_user_access(current_user, user_id)
    await delete_inline_response(
        db,
        article_id=article_id,
        user_id=user_id,
        inline_response_id=inline_response_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
