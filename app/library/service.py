import uuid
from collections import Counter, defaultdict
from datetime import timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models import Article, ArticleTag, Tag
from app.articles.schemas import ArticleAuthor, ArticleListResponse, SaveArticleResponse
from app.articles.service import build_article_summaries, unsave_article as unsave_article_service
from app.auth.models import User
from app.common.exceptions import not_found
from app.common.pagination import PaginationMeta, paginate_scalars
from app.highlights.models import Highlight
from app.highlights.schemas import HighlightItem, HighlightListResponse
from app.library.models import ReadingHistory, SavedArticle
from app.library.schemas import (
    AnalyticsTagCount,
    MonthlyBreakdownItem,
    ReadingAnalyticsResponse,
    ReadingHistoryEntry,
    ReadingHistoryListResponse,
    ReadingStreak,
)
from app.responses.models import Response
from app.responses.schemas import ResponseItem, ResponseListResponse


async def _get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise not_found("User not found.")
    return user


async def list_library_highlights(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    limit: int,
) -> HighlightListResponse:
    await _get_user_or_404(db, user_id)
    highlights, pagination = await paginate_scalars(
        db,
        select(Highlight).where(Highlight.user_id == user_id).order_by(Highlight.created_at.desc()),
        page,
        limit,
    )
    article_ids = [highlight.article_id for highlight in highlights]
    article_map = {}
    if article_ids:
        article_map = {
            article.id: article
            for article in (await db.scalars(select(Article).where(Article.id.in_(article_ids)))).all()
        }

    data = [
        HighlightItem(
            id=highlight.id,
            article_id=highlight.article_id,
            article_title=article_map[highlight.article_id].title if highlight.article_id in article_map else "",
            text=highlight.text,
            color=highlight.color,
            date=highlight.created_at.date(),
            paragraph_index=highlight.paragraph_index,
        )
        for highlight in highlights
    ]
    return HighlightListResponse(data=data, pagination=pagination)


async def delete_library_highlight(db: AsyncSession, user_id: uuid.UUID, highlight_id: uuid.UUID) -> None:
    highlight = await db.get(Highlight, highlight_id)
    if highlight is None or highlight.user_id != user_id:
        raise not_found("Highlight not found.")
    await db.delete(highlight)
    await db.commit()


async def list_saved_articles(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    limit: int,
) -> ArticleListResponse:
    await _get_user_or_404(db, user_id)
    articles, pagination = await paginate_scalars(
        db,
        select(Article)
        .join(SavedArticle, SavedArticle.article_id == Article.id)
        .where(SavedArticle.user_id == user_id)
        .order_by(SavedArticle.saved_at.desc()),
        page,
        limit,
    )
    return ArticleListResponse(data=await build_article_summaries(db, articles), pagination=pagination)


async def get_saved_article_state(
    db: AsyncSession,
    user_id: uuid.UUID,
    article_id: uuid.UUID,
) -> SaveArticleResponse:
    await _get_user_or_404(db, user_id)
    saved_article = await db.scalar(
        select(SavedArticle.article_id).where(
            SavedArticle.user_id == user_id,
            SavedArticle.article_id == article_id,
        )
    )
    return SaveArticleResponse(saved=saved_article is not None, article_id=article_id)


async def unsave_article(db: AsyncSession, user_id: uuid.UUID, article_id: uuid.UUID) -> None:
    await unsave_article_service(db, article_id=article_id, user_id=user_id)


async def list_reading_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    limit: int,
) -> ReadingHistoryListResponse:
    await _get_user_or_404(db, user_id)

    # Subquery: for each article, find the latest read_at
    latest_sub = (
        select(
            ReadingHistory.article_id,
            func.max(ReadingHistory.read_at).label("max_read_at"),
        )
        .where(ReadingHistory.user_id == user_id)
        .group_by(ReadingHistory.article_id)
        .subquery()
    )

    # Join back to get the full row for each article's latest entry
    stmt = (
        select(ReadingHistory)
        .join(
            latest_sub,
            (ReadingHistory.article_id == latest_sub.c.article_id)
            & (ReadingHistory.read_at == latest_sub.c.max_read_at),
        )
        .where(ReadingHistory.user_id == user_id)
        .order_by(ReadingHistory.read_at.desc())
    )

    entries, pagination = await paginate_scalars(
        db,
        stmt,
        page,
        limit,
    )
    article_ids = [entry.article_id for entry in entries]
    article_map = {}
    if article_ids:
        article_map = {
            article.id: article
            for article in (await db.scalars(select(Article).where(Article.id.in_(article_ids)))).all()
        }
    tag_map: dict[uuid.UUID, list[str]] = defaultdict(list)
    if article_ids:
        tag_rows = await db.execute(
            select(ArticleTag.article_id, Tag.name)
            .join(Tag, Tag.id == ArticleTag.tag_id)
            .where(ArticleTag.article_id.in_(article_ids))
        )
        for article_id, tag_name in tag_rows.all():
            tag_map[article_id].append(tag_name)

    data = [
        ReadingHistoryEntry(
            id=str(entry.id),
            article_id=str(entry.article_id),
            title=article_map[entry.article_id].title if entry.article_id in article_map else "",
            date=str(entry.read_at.date()),
            time_spent=entry.time_spent,
            read_percentage=entry.read_percentage,
            tags=sorted(tag_map.get(entry.article_id, [])),
        )
        for entry in entries
    ]
    return ReadingHistoryListResponse(data=data, pagination=pagination)


async def delete_history_entry(db: AsyncSession, user_id: uuid.UUID, history_id: uuid.UUID) -> None:
    entry = await db.get(ReadingHistory, history_id)
    if entry is None or entry.user_id != user_id:
        raise not_found("Reading history entry not found.")
    await db.delete(entry)
    await db.commit()


async def list_user_responses(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    limit: int,
) -> ResponseListResponse:
    user = await _get_user_or_404(db, user_id)
    responses, pagination = await paginate_scalars(
        db,
        select(Response).where(Response.user_id == user_id).order_by(Response.created_at.desc()),
        page,
        limit,
    )
    article_ids = [response.article_id for response in responses]
    article_map = {}
    if article_ids:
        article_map = {
            article.id: article
            for article in (await db.scalars(select(Article).where(Article.id.in_(article_ids)))).all()
        }
    author = ArticleAuthor(id=user.id, name=user.name, avatar=user.avatar, bio=user.bio)
    data = [
        ResponseItem(
            id=response.id,
            article_id=response.article_id,
            article_title=article_map[response.article_id].title if response.article_id in article_map else "",
            text=response.text,
            date=response.created_at.date(),
            likes=response.likes,
            author=author,
        )
        for response in responses
    ]
    return ResponseListResponse(data=data, pagination=pagination)


async def delete_library_response(
    db: AsyncSession,
    user_id: uuid.UUID,
    article_id: uuid.UUID,
    response_id: uuid.UUID,
) -> None:
    response = await db.get(Response, response_id)
    if response is None or response.user_id != user_id or response.article_id != article_id:
        raise not_found("Response not found.")
    article = await db.get(Article, article_id)
    if article is not None:
        article.response_count = max(article.response_count - 1, 0)
    await db.delete(response)
    await db.commit()


def _compute_streaks(days: list) -> ReadingStreak:
    if not days:
        return ReadingStreak(current_days=0, longest_days=0)

    unique_days = sorted(set(days))
    longest = 1
    run = 1
    for index in range(1, len(unique_days)):
        if unique_days[index] - unique_days[index - 1] == timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    current = 1
    latest = unique_days[-1]
    for index in range(len(unique_days) - 2, -1, -1):
        if latest - unique_days[index] == timedelta(days=current):
            current += 1
        else:
            break
    return ReadingStreak(current_days=current, longest_days=longest)


async def get_reading_analytics(db: AsyncSession, user_id: uuid.UUID) -> ReadingAnalyticsResponse:
    await _get_user_or_404(db, user_id)

    # Aggregate per article: take max time_spent, max read_percentage, latest read_at
    per_article_sub = (
        select(
            ReadingHistory.article_id,
            func.max(ReadingHistory.time_spent).label("best_time"),
            func.max(ReadingHistory.read_percentage).label("best_pct"),
            func.max(ReadingHistory.read_at).label("latest_read_at"),
        )
        .where(ReadingHistory.user_id == user_id)
        .group_by(ReadingHistory.article_id)
        .subquery()
    )

    rows = (await db.execute(select(per_article_sub))).all()

    total_articles_read = len(rows)
    total_time_spent = sum(r.best_time for r in rows)
    average_time = round(total_time_spent / total_articles_read) if total_articles_read else 0
    total_read_pct = sum(r.best_pct for r in rows)
    average_read_pct = round(total_read_pct / total_articles_read) if total_articles_read else 0

    article_ids = [r.article_id for r in rows]
    tag_counter: Counter[str] = Counter()
    if article_ids:
        tag_rows = await db.execute(
            select(Tag.name)
            .join(ArticleTag, ArticleTag.tag_id == Tag.id)
            .where(ArticleTag.article_id.in_(article_ids))
        )
        tag_counter.update(tag_name for (tag_name,) in tag_rows.all())

    top_tags = [AnalyticsTagCount(tag=tag, count=count) for tag, count in tag_counter.most_common(5)]
    reading_streak = _compute_streaks([r.latest_read_at.date() for r in rows])

    monthly: dict[str, dict[str, int]] = defaultdict(lambda: {"articles": 0, "time": 0})
    for r in rows:
        month = r.latest_read_at.strftime("%Y-%m")
        monthly[month]["articles"] += 1
        monthly[month]["time"] += r.best_time

    monthly_breakdown = [
        MonthlyBreakdownItem(
            month=month,
            articles_read=values["articles"],
            time_spent_minutes=values["time"],
        )
        for month, values in sorted(monthly.items(), reverse=True)
    ]

    return ReadingAnalyticsResponse(
        total_articles_read=total_articles_read,
        total_time_spent_minutes=total_time_spent,
        average_reading_time_minutes=average_time,
        average_read_percentage=average_read_pct,
        top_tags=top_tags,
        reading_streak=reading_streak,
        monthly_breakdown=monthly_breakdown,
    )
