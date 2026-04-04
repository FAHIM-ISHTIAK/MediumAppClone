import uuid
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


CONTENT_TYPE = JSON().with_variant(JSONB, "postgresql")


class Article(TimestampMixin, Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index("idx_articles_created", "created_at"),
        Index("idx_articles_clap_count", "clap_count"),
        Index("idx_articles_author", "author_id"),
        Index("idx_articles_publication", "publication_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    publication_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("publications.id", ondelete="SET NULL"),
        nullable=True,
    )
    content: Mapped[list[str]] = mapped_column(CONTENT_TYPE, nullable=False)
    cover_image: Mapped[str | None] = mapped_column(Text, nullable=True)
    reading_time: Mapped[int] = mapped_column(Integer, nullable=False)
    clap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    response_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class ArticleTag(Base):
    __tablename__ = "article_tags"

    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Clap(TimestampMixin, Base):
    __tablename__ = "claps"
    __table_args__ = (
        CheckConstraint("count >= 1", name="clap_count_min"),
        Index("idx_claps_article_user", "article_id", "user_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
