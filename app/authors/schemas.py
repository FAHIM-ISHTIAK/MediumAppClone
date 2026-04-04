import uuid

from app.common.pagination import PaginationMeta
from app.common.schemas import APIModel


class Author(APIModel):
    id: uuid.UUID
    name: str
    avatar: str | None = None
    bio: str | None = None
    followers: int
    following: int
    articles: int
    is_following: bool = False


class AuthorListResponse(APIModel):
    data: list[Author]
    pagination: PaginationMeta


class FollowingItem(APIModel):
    name: str
    avatar: str | None = None
    type: str


class FollowingListResponse(APIModel):
    data: list[FollowingItem]
    pagination: PaginationMeta


class FollowStateResponse(APIModel):
    following: bool
    follower_count: int
