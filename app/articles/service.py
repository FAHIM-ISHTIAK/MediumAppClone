import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models import Article, ArticleTag, Clap, Tag
from app.articles.schemas import Article as ArticleSchema
from app.articles.schemas import ArticleAuthor, ArticleListResponse, ArticleSummary
from app.articles.schemas import ClapArticleResponse, SaveArticleResponse
from app.auth.models import User
from app.common.exceptions import bad_request, forbidden, not_found
from app.common.pagination import PaginationMeta, paginate_scalars
from app.library.models import ReadingHistory, SavedArticle
from app.publications.models import Publication


def estimate_reading_time(content: list[str]) -> int:
    words = sum(len((paragraph or "").split()) for paragraph in content)
    return max(1, round(words / 200))


async def get_article_or_404(db: AsyncSession, article_id: uuid.UUID) -> Article:
    article = await db.get(Article, article_id)
    if article is None:
        raise not_found("Article not found.")
    return article


async def _get_users_map(db: AsyncSession, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, User]:
    if not user_ids:
        return {}
    result = await db.scalars(select(User).where(User.id.in_(user_ids)))
    return {user.id: user for user in result.all()}


async def _get_publications_map(
    db: AsyncSession,
    publication_ids: list[uuid.UUID],
) -> dict[uuid.UUID, Publication]:
    if not publication_ids:
        return {}
    result = await db.scalars(select(Publication).where(Publication.id.in_(publication_ids)))
    return {publication.id: publication for publication in result.all()}


async def _get_tags_map(
    db: AsyncSession,
    article_ids: list[uuid.UUID],
) -> dict[uuid.UUID, list[str]]:
    if not article_ids:
        return {}

    result = await db.execute(
        select(ArticleTag.article_id, Tag.name)
        .join(Tag, Tag.id == ArticleTag.tag_id)
        .where(ArticleTag.article_id.in_(article_ids))
        .order_by(Tag.name.asc())
    )

    tag_map: dict[uuid.UUID, list[str]] = {article_id: [] for article_id in article_ids}
    for article_id, tag_name in result.all():
        tag_map.setdefault(article_id, []).append(tag_name)
    return tag_map


def _author_payload(user: User) -> ArticleAuthor:
    return ArticleAuthor(id=user.id, name=user.name, avatar=user.avatar, bio=user.bio)


async def build_article_summaries(
    db: AsyncSession,
    articles: list[Article],
) -> list[ArticleSummary]:
    user_map = await _get_users_map(db, [article.author_id for article in articles])
    publication_map = await _get_publications_map(
        db,
        [article.publication_id for article in articles if article.publication_id],
    )
    tag_map = await _get_tags_map(db, [article.id for article in articles])

    summaries: list[ArticleSummary] = []
    for article in articles:
        author = user_map.get(article.author_id)
        if author is None:
            continue
        publication = publication_map.get(article.publication_id) if article.publication_id else None
        summaries.append(
            ArticleSummary(
                id=article.id,
                title=article.title,
                subtitle=article.subtitle,
                author=_author_payload(author),
                publication=publication.name if publication else None,
                reading_time=article.reading_time,
                tags=tag_map.get(article.id, []),
                claps=article.clap_count,
                date=article.created_at.date(),
                cover_image=article.cover_image,
            )
        )
    return summaries


async def build_article_detail(db: AsyncSession, article: Article) -> ArticleSchema:
    user_map = await _get_users_map(db, [article.author_id])
    publication_map = await _get_publications_map(
        db,
        [article.publication_id] if article.publication_id else [],
    )
    tag_map = await _get_tags_map(db, [article.id])
    author = user_map.get(article.author_id)
    if author is None:
        raise not_found("Article author not found.")
    publication = publication_map.get(article.publication_id) if article.publication_id else None
    return ArticleSchema(
        id=article.id,
        title=article.title,
        subtitle=article.subtitle,
        author=_author_payload(author),
        publication=publication.name if publication else None,
        reading_time=article.reading_time,
        tags=tag_map.get(article.id, []),
        claps=article.clap_count,
        date=article.created_at.date(),
        content=article.content,
        cover_image=article.cover_image,
    )


def _recommended_score_expr(dialect_name: str):
    if dialect_name == "sqlite":
        days_old = func.max(
            func.julianday(func.current_timestamp()) - func.julianday(Article.created_at),
            0.0,
        )
    else:
        days_old = func.greatest(
            func.extract("epoch", func.now() - Article.created_at) / 86400.0,
            0.0,
        )

    recency_score = 100.0 / (1.0 + days_old)
    return cast(Article.clap_count, Float) * 0.3 + recency_score * 0.7


async def list_articles(
    db: AsyncSession,
    tag: str | None,
    sort: str,
    page: int,
    limit: int,
) -> ArticleListResponse:
    dialect_name = db.get_bind().dialect.name
    stmt = select(Article)
    if tag:
        stmt = (
            stmt.join(ArticleTag, ArticleTag.article_id == Article.id)
            .join(Tag, Tag.id == ArticleTag.tag_id)
            .where(func.lower(Tag.name) == tag.lower())
        )

    if sort == "latest":
        articles, pagination = await paginate_scalars(db, stmt.order_by(Article.created_at.desc()), page, limit)
    elif sort == "popular":
        articles, pagination = await paginate_scalars(db, stmt.order_by(Article.clap_count.desc(), Article.created_at.desc()), page, limit)
    else:
        articles, pagination = await paginate_scalars(
            db,
            stmt.order_by(_recommended_score_expr(dialect_name).desc(), Article.created_at.desc()),
            page,
            limit,
        )

    summaries = await build_article_summaries(db, articles)
    return ArticleListResponse(data=summaries, pagination=pagination)


async def _upsert_reading_history(
    db: AsyncSession,
    *,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    time_spent: int | None = None,
    read_percentage: int | None = None,
) -> ReadingHistory:
    threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
    history_stmt = (
        select(ReadingHistory)
        .where(
            ReadingHistory.user_id == user_id,
            ReadingHistory.article_id == article_id,
            ReadingHistory.read_at >= threshold,
        )
        .order_by(ReadingHistory.read_at.desc())
        .limit(1)
    )
    history = await db.scalar(history_stmt)
    if history is None:
        history = ReadingHistory(
            user_id=user_id,
            article_id=article_id,
            time_spent=max(time_spent or 0, 0),
            read_percentage=max(min(read_percentage or 0, 100), 0),
        )
        db.add(history)
    else:
        if time_spent is not None:
            history.time_spent = max(time_spent, 0)
        if read_percentage is not None:
            history.read_percentage = max(min(read_percentage, 100), max(history.read_percentage, 0))
    await db.commit()
    await db.refresh(history)
    return history


async def get_article(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
    time_spent: int | None = None,
) -> ArticleSchema:
    article = await get_article_or_404(db, article_id)
    if user_id is not None:
        await _upsert_reading_history(db, article_id=article.id, user_id=user_id, time_spent=time_spent)
    return await build_article_detail(db, article)


async def clap_article(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    count: int,
) -> ClapArticleResponse:
    if count < 1:
        raise bad_request("Clap count must be at least 1.")

    article = await get_article_or_404(db, article_id)
    user = await db.get(User, user_id)
    if user is None:
        raise not_found("User not found.")

    clap = await db.scalar(
        select(Clap).where(Clap.article_id == article_id, Clap.user_id == user_id)
    )
    if clap is None:
        clap = Clap(article_id=article_id, user_id=user_id, count=count)
        db.add(clap)
        delta = count
    else:
        clap.count += count
        delta = count

    article.clap_count += delta
    await db.commit()
    await db.refresh(article)
    return ClapArticleResponse(total_claps=article.clap_count)


async def track_article_reading(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
    time_spent: int,
    read_percentage: int = 0,
) -> dict[str, bool]:
    await get_article_or_404(db, article_id)
    await _upsert_reading_history(
        db,
        article_id=article_id,
        user_id=user_id,
        time_spent=time_spent,
        read_percentage=read_percentage,
    )
    return {"tracked": True}


async def save_article(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
) -> SaveArticleResponse:
    await get_article_or_404(db, article_id)
    saved = await db.scalar(
        select(SavedArticle).where(
            SavedArticle.user_id == user_id,
            SavedArticle.article_id == article_id,
        )
    )
    if saved is None:
        db.add(SavedArticle(user_id=user_id, article_id=article_id))
        await db.commit()
    return SaveArticleResponse(saved=True, article_id=article_id)


async def unsave_article(
    db: AsyncSession,
    article_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    saved = await db.scalar(
        select(SavedArticle).where(
            SavedArticle.user_id == user_id,
            SavedArticle.article_id == article_id,
        )
    )
    if saved is None:
        raise not_found("Saved article not found.")
    await db.delete(saved)
    await db.commit()
