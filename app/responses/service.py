import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models import Article
from app.articles.schemas import ArticleAuthor
from app.auth.models import User
from app.common.exceptions import forbidden, not_found
from app.common.pagination import paginate_scalars
from app.responses.models import InlineResponse, Response
from app.responses.schemas import (
    InlineResponseItem,
    InlineResponseListResponse,
    ResponseItem,
    ResponseListResponse,
)


async def _get_response_author(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise not_found("User not found.")
    return user


async def _get_response_authors_map(
    db: AsyncSession,
    user_ids: list[uuid.UUID],
) -> dict[uuid.UUID, User]:
    if not user_ids:
        return {}

    users = (
        await db.scalars(
            select(User).where(User.id.in_(user_ids))
        )
    ).all()
    return {user.id: user for user in users}


def _author_payload(user: User) -> ArticleAuthor:
    return ArticleAuthor(id=user.id, name=user.name, avatar=user.avatar, bio=user.bio)


async def _get_article(db: AsyncSession, article_id: uuid.UUID) -> Article:
    article = await db.get(Article, article_id)
    if article is None:
        raise not_found("Article not found.")
    return article


async def list_responses(
    db: AsyncSession,
    article_id: uuid.UUID,
    page: int,
    limit: int,
) -> ResponseListResponse:
    article = await _get_article(db, article_id)
    responses, pagination = await paginate_scalars(
        db,
        select(Response).where(Response.article_id == article_id).order_by(Response.created_at.desc()),
        page,
        limit,
    )
    authors = await _get_response_authors_map(db, [response.user_id for response in responses])

    data: list[ResponseItem] = []
    for response in responses:
        author = authors.get(response.user_id)
        if author is None:
            continue
        data.append(
            ResponseItem(
                id=response.id,
                article_id=response.article_id,
                article_title=article.title,
                text=response.text,
                date=response.created_at.date(),
                likes=response.likes,
                author=_author_payload(author),
            )
        )

    return ResponseListResponse(data=data, pagination=pagination)


async def create_response(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    text: str,
) -> ResponseItem:
    article = await _get_article(db, article_id)
    author = await _get_response_author(db, user_id)
    response = Response(article_id=article_id, user_id=user_id, text=text)
    article.response_count += 1
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return ResponseItem(
        id=response.id,
        article_id=response.article_id,
        article_title=article.title,
        text=response.text,
        date=response.created_at.date(),
        likes=response.likes,
        author=_author_payload(author),
    )


async def update_response(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    response_id: uuid.UUID,
    text: str,
) -> ResponseItem:
    article = await _get_article(db, article_id)
    response = await db.get(Response, response_id)
    if response is None or response.article_id != article_id:
        raise not_found("Response not found.")
    if response.user_id != user_id:
        raise forbidden("Only the response owner can update this response.")
    response.text = text
    await db.commit()
    await db.refresh(response)
    author = await _get_response_author(db, response.user_id)
    return ResponseItem(
        id=response.id,
        article_id=response.article_id,
        article_title=article.title,
        text=response.text,
        date=response.updated_at.date(),
        likes=response.likes,
        author=_author_payload(author),
    )


async def delete_response(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    response_id: uuid.UUID,
) -> None:
    article = await _get_article(db, article_id)
    response = await db.get(Response, response_id)
    if response is None or response.article_id != article_id:
        raise not_found("Response not found.")
    if response.user_id != user_id:
        raise forbidden("Only the response owner can delete this response.")
    article.response_count = max(article.response_count - 1, 0)
    await db.delete(response)
    await db.commit()


async def clap_response(
    db: AsyncSession,
    article_id: uuid.UUID,
    response_id: uuid.UUID,
    count: int,
) -> int:
    await _get_article(db, article_id)
    response = await db.get(Response, response_id)
    if response is None or response.article_id != article_id:
        raise not_found("Response not found.")

    response.likes += count
    await db.commit()
    await db.refresh(response)
    return response.likes


async def list_inline_responses(
    db: AsyncSession,
    article_id: uuid.UUID,
    page: int,
    limit: int,
) -> InlineResponseListResponse:
    await _get_article(db, article_id)
    responses, pagination = await paginate_scalars(
        db,
        select(InlineResponse)
        .where(InlineResponse.article_id == article_id)
        .order_by(InlineResponse.created_at.desc()),
        page,
        limit,
    )
    data = [
        InlineResponseItem(
            id=response.id,
            article_id=response.article_id,
            user_id=response.user_id,
            selected_text=response.selected_text,
            paragraph_index=response.paragraph_index,
            text=response.text,
            date=response.created_at.date(),
            likes=response.likes,
        )
        for response in responses
    ]
    return InlineResponseListResponse(data=data, pagination=pagination)


async def create_inline_response(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    selected_text: str,
    paragraph_index: int,
    text: str,
) -> InlineResponseItem:
    await _get_article(db, article_id)
    response = InlineResponse(
        article_id=article_id,
        user_id=user_id,
        selected_text=selected_text,
        paragraph_index=paragraph_index,
        text=text,
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return InlineResponseItem(
        id=response.id,
        article_id=response.article_id,
        user_id=response.user_id,
        selected_text=response.selected_text,
        paragraph_index=response.paragraph_index,
        text=response.text,
        date=response.created_at.date(),
        likes=response.likes,
    )


async def update_inline_response(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    inline_response_id: uuid.UUID,
    text: str,
) -> InlineResponseItem:
    await _get_article(db, article_id)
    response = await db.get(InlineResponse, inline_response_id)
    if response is None or response.article_id != article_id:
        raise not_found("Inline response not found.")
    if response.user_id != user_id:
        raise forbidden("Only the inline response owner can update this response.")
    response.text = text
    await db.commit()
    await db.refresh(response)
    return InlineResponseItem(
        id=response.id,
        article_id=response.article_id,
        user_id=response.user_id,
        selected_text=response.selected_text,
        paragraph_index=response.paragraph_index,
        text=response.text,
        date=response.updated_at.date(),
        likes=response.likes,
    )


async def delete_inline_response(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    inline_response_id: uuid.UUID,
) -> None:
    await _get_article(db, article_id)
    response = await db.get(InlineResponse, inline_response_id)
    if response is None or response.article_id != article_id:
        raise not_found("Inline response not found.")
    if response.user_id != user_id:
        raise forbidden("Only the inline response owner can delete this response.")
    await db.delete(response)
    await db.commit()
