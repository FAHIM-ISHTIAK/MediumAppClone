import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models import Article
from app.common.exceptions import forbidden, not_found
from app.common.pagination import paginate_scalars
from app.highlights.models import Highlight
from app.highlights.schemas import HighlightItem, HighlightListResponse


async def _get_article(db: AsyncSession, article_id: uuid.UUID) -> Article:
    article = await db.get(Article, article_id)
    if article is None:
        raise not_found("Article not found.")
    return article


async def list_article_highlights(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 100,
) -> HighlightListResponse:
    article = await _get_article(db, article_id)
    highlights, pagination = await paginate_scalars(
        db,
        select(Highlight)
        .where(Highlight.article_id == article_id, Highlight.user_id == user_id)
        .order_by(Highlight.created_at.desc()),
        page,
        limit,
    )
    data = [
        HighlightItem(
            id=highlight.id,
            article_id=highlight.article_id,
            article_title=article.title,
            text=highlight.text,
            color=highlight.color,
            date=highlight.created_at.date(),
            paragraph_index=highlight.paragraph_index,
        )
        for highlight in highlights
    ]
    return HighlightListResponse(data=data, pagination=pagination)


async def create_highlight(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    text: str,
    color: str,
    paragraph_index: int | None,
) -> HighlightItem:
    article = await _get_article(db, article_id)
    highlight = Highlight(
        article_id=article_id,
        user_id=user_id,
        text=text,
        color=color,
        paragraph_index=paragraph_index,
    )
    db.add(highlight)
    await db.commit()
    await db.refresh(highlight)
    return HighlightItem(
        id=highlight.id,
        article_id=highlight.article_id,
        article_title=article.title,
        text=highlight.text,
        color=highlight.color,
        date=highlight.created_at.date(),
        paragraph_index=highlight.paragraph_index,
    )


async def delete_highlight(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    highlight_id: uuid.UUID,
) -> None:
    await _get_article(db, article_id)
    highlight = await db.get(Highlight, highlight_id)
    if highlight is None or highlight.article_id != article_id:
        raise not_found("Highlight not found.")
    if highlight.user_id != user_id:
        raise forbidden("Only the highlight owner can delete this highlight.")
    await db.delete(highlight)
    await db.commit()
