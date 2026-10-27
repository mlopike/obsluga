"""Зависимости аутентификации и авторизации."""
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.security import decode_token
from app.database import async_session
from app.models.account import Account

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_account(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> Account:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не предоставлен токен",
        )
    payload = decode_token(credentials.credentials)
    result = await db.execute(
        select(Account)
        .where(Account.account_id == int(payload["sub"]))
        .options(joinedload(Account.role))
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Аккаунт не найден",
        )
    return account


CurrentAccount = Annotated[Account, Depends(get_current_account)]


def require_perm(level: int):
    """Фабрика зависимости прав: 403 при perm_level < level."""

    async def check_permission(account: CurrentAccount) -> Account:
        if account.role.perm_level < level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав",
            )
        return account

    return check_permission
