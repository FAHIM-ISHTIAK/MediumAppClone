import uuid

from sqlalchemy import func, select
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
    # Only fetch top-level responses (no parent)
    responses, pagination = await paginate_scalars(
        db,
        select(Response)
        .where(Response.article_id == article_id, Response.parent_id.is_(None))
        .order_by(Response.created_at.desc()),
        page,
        limit,
    )
    # Count replies per top-level response
    response_ids = [r.id for r in responses]
    reply_counts: dict[uuid.UUID, int] = {}
    if response_ids:
        rows = (
            await db.execute(
                select(Response.parent_id, func.count())
                .where(Response.parent_id.in_(response_ids))
                .group_by(Response.parent_id)
            )
        ).all()
        reply_counts = {row[0]: row[1] for row in rows}

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
                parent_id=response.parent_id,
                reply_count=reply_counts.get(response.id, 0),
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
        parent_id=None,
        reply_count=0,
    )


async def create_reply(
    db: AsyncSession,
    article_id: uuid.UUID,
    parent_id: uuid.UUID,
    user_id: uuid.UUID,
    text: str,
) -> ResponseItem:
    article = await _get_article(db, article_id)
    parent = await db.get(Response, parent_id)
    if parent is None or parent.article_id != article_id:
        raise not_found("Parent response not found.")
    author = await _get_response_author(db, user_id)
    response = Response(article_id=article_id, user_id=user_id, text=text, parent_id=parent_id)
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
        parent_id=response.parent_id,
        reply_count=0,
    )


async def list_replies(
    db: AsyncSession,
    article_id: uuid.UUID,
    parent_id: uuid.UUID,
    page: int,
    limit: int,
) -> ResponseListResponse:
    article = await _get_article(db, article_id)
    parent = await db.get(Response, parent_id)
    if parent is None or parent.article_id != article_id:
        raise not_found("Parent response not found.")

    responses, pagination = await paginate_scalars(
        db,
        select(Response)
        .where(Response.parent_id == parent_id)
        .order_by(Response.created_at.asc()),
        page,
        limit,
    )
    # Count nested replies for each reply
    response_ids = [r.id for r in responses]
    reply_counts: dict[uuid.UUID, int] = {}
    if response_ids:
        rows = (
            await db.execute(
                select(Response.parent_id, func.count())
                .where(Response.parent_id.in_(response_ids))
                .group_by(Response.parent_id)
            )
        ).all()
        reply_counts = {row[0]: row[1] for row in rows}

    authors = await _get_response_authors_map(db, [r.user_id for r in responses])
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
                parent_id=response.parent_id,
                reply_count=reply_counts.get(response.id, 0),
            )
        )
    return ResponseListResponse(data=data, pagination=pagination)


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
    reply_count = (
        await db.scalar(
            select(func.count()).select_from(Response).where(Response.parent_id == response.id)
        )
    ) or 0
    return ResponseItem(
        id=response.id,
        article_id=response.article_id,
        article_title=article.title,
        text=response.text,
        date=response.updated_at.date(),
        likes=response.likes,
        author=_author_payload(author),
        parent_id=response.parent_id,
        reply_count=reply_count,
    )


async def _count_descendants(db: AsyncSession, response_id: uuid.UUID) -> int:
    """Recursively count all nested replies under a response."""
    children = (
        await db.scalars(
            select(Response).where(Response.parent_id == response_id)
        )
    ).all()
    count = len(children)
    for child in children:
        count += await _count_descendants(db, child.id)
    return count


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
    # Count this response + all nested descendants
    descendant_count = await _count_descendants(db, response_id)
    total_deleted = 1 + descendant_count
    article.response_count = max(article.response_count - total_deleted, 0)
    # CASCADE FK will remove all children
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
    user_id: uuid.UUID | None = None,
) -> InlineResponseListResponse:
    await _get_article(db, article_id)
    stmt = select(InlineResponse).where(InlineResponse.article_id == article_id)
    if user_id is not None:
        stmt = stmt.where(InlineResponse.user_id == user_id)
    responses, pagination = await paginate_scalars(
        db,
        stmt.order_by(InlineResponse.created_at.desc()),
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
