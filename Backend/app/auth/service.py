import uuid
import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from functools import lru_cache

from app.auth.models import User
from app.config import settings

@lru_cache()
def get_jwks():
    if not settings.supabase_url:
        return {"keys": []}
    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    response = httpx.get(jwks_url)
    response.raise_for_status()
    return response.json()

def verify_supabase_token(token: str) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg")

        if alg == "HS256":
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )

        if alg != "ES256":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported token algorithm.",
            )

        jwks = get_jwks()
        public_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                public_key = key
                break

        if not public_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Public key not found in JWKS")

        return jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            issuer=f"{settings.supabase_url}/auth/v1",
            options={"verify_aud": False}
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token verification failed: {str(exc)}") from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed") from exc

async def sync_user(db: AsyncSession, token_payload: dict) -> User:
    user_id = uuid.UUID(token_payload["sub"])
    email = token_payload.get("email", "")
    metadata = token_payload.get("user_metadata", {}) or {}
    name = metadata.get("full_name") or metadata.get("name") or email.split("@")[0]
    avatar = metadata.get("avatar_url") or metadata.get("picture")

    user = await db.get(User, user_id)
    if user is None:
        user = User(id=user_id, email=email, name=name, avatar=avatar)
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            user = await db.get(User, user_id)
            user.email = email
            user.name = name
            user.avatar = avatar
            await db.commit()
    else:
        user.email = email
        user.name = name
        user.avatar = avatar
        await db.commit()

    await db.refresh(user)
    return user
