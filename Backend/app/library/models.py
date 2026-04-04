import uuid

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SavedArticle(Base):
    __tablename__ = "saved_articles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ReadingHistory(Base):
    __tablename__ = "reading_history"
    __table_args__ = (Index("idx_reading_history_user", "user_id", "read_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    time_spent: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    read_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
