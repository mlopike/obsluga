"""Хеширование паролей (bcrypt) и JWT-токены (HS256)."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.config import Settings

settings = Settings()

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(
    account_id: int,
    perm_level: int,
    department_id: int,
    full_name: str,
    remember: bool = False,
) -> str:
    now = datetime.now(timezone.utc)
    hours = settings.token_hours_remember if remember else settings.token_hours
    payload = {
        "sub": str(account_id),
        "perm": perm_level,
        "dept": department_id,
        "name": full_name,
        "exp": now + timedelta(hours=hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен недействительный или просрочен",
        )
