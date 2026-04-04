from app.common.pagination import PaginationMeta
from app.common.schemas import APIModel


class SearchSection(APIModel):
    data: list
    total: int


class SearchResponse(APIModel):
    stories: SearchSection | None = None
    people: SearchSection | None = None
    publications: SearchSection | None = None
    pagination: PaginationMeta
