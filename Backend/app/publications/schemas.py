import uuid

from app.common.pagination import PaginationMeta
from app.common.schemas import APIModel


class Publication(APIModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    avatar: str | None = None
    followers: int
    articles_count: int


class PublicationListResponse(APIModel):
    data: list[Publication]
    pagination: PaginationMeta


class FollowPublicationResponse(APIModel):
    following: bool
    follower_count: int
