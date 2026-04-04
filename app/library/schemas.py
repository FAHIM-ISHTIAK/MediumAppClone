from app.common.pagination import PaginationMeta
from app.common.schemas import APIModel


class ReadingHistoryEntry(APIModel):
    id: str
    article_id: str
    title: str
    date: str
    time_spent: int
    read_percentage: int
    tags: list[str]


class ReadingHistoryListResponse(APIModel):
    data: list[ReadingHistoryEntry]
    pagination: PaginationMeta


class AnalyticsTagCount(APIModel):
    tag: str
    count: int


class ReadingStreak(APIModel):
    current_days: int
    longest_days: int


class MonthlyBreakdownItem(APIModel):
    month: str
    articles_read: int
    time_spent_minutes: int


class ReadingAnalyticsResponse(APIModel):
    total_articles_read: int
    total_time_spent_minutes: int
    average_reading_time_minutes: int
    average_read_percentage: int
    top_tags: list[AnalyticsTagCount]
    reading_streak: ReadingStreak
    monthly_breakdown: list[MonthlyBreakdownItem]
