import uuid
from datetime import datetime

from app.common.schemas import APIModel


class UserInfo(APIModel):
    id: uuid.UUID
    email: str
    name: str
    avatar: str | None = None
    bio: str | None = None
    created_at: datetime
    updated_at: datetime
