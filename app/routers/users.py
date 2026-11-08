"""Управление пользователями — только для администратора."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.core.deps import DbSession, require_roles
from app.core.roles import PERM_ADMIN, PERM_ENGINEER, ROLE_EMPLOYEE, ROLE_ENGINEER
from app.models.account import Account
from app.models.request import Request
from app.models.role import Role
from app.schemas.auth import UserOut, UserRolePatch

router = APIRouter(dependencies=[Depends(require_roles(PERM_ADMIN))])


def _to_user(account: Account) -> UserOut:
    return UserOut(
        id=account.account_id,
        full_name=account.full_name,
        email=account.email,
        role=account.role.name,
        perm=account.role.perm_level,
        department=account.department.name,
    )


@router.get("", response_model=list[UserOut])
async def list_users(db: DbSession, role: Optional[str] = None) -> list[UserOut]:
    query = (
        select(Account)
        .join(Role, Account.role_id == Role.role_id)
        .options(joinedload(Account.role), joinedload(Account.department))
        .order_by(Account.full_name)
    )
    if role:
        query = query.where(Role.name == role)
    result = await db.execute(query)
    return [_to_user(account) for account in result.scalars().all()]


@router.patch("/{account_id}", response_model=UserOut)
async def change_role(account_id: int, data: UserRolePatch, db: DbSession) -> UserOut:
    """Назначает сотруднику роль инженера и обратно. Роль администратора не меняется."""
    if data.role not in (ROLE_EMPLOYEE, ROLE_ENGINEER):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Допустимые роли: {ROLE_EMPLOYEE}, {ROLE_ENGINEER}",
        )
    account = (
        await db.execute(
            select(Account)
            .where(Account.account_id == account_id)
            .options(joinedload(Account.role), joinedload(Account.department))
        )
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if account.role.perm_level == PERM_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Роль администратора изменить нельзя")

    if account.role.name == ROLE_ENGINEER and data.role == ROLE_EMPLOYEE:
        open_count = (
            await db.execute(
                select(func.count())
                .select_from(Request)
                .where(Request.engineer_id == account_id, Request.status != "closed")
            )
        ).scalar_one()
        if open_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"У инженера есть незакрытые заявки ({open_count}). Сначала переназначьте их",
            )

    role = (await db.execute(select(Role).where(Role.name == data.role))).scalar_one()
    account.role_id = role.role_id
    await db.commit()
    await db.refresh(account, attribute_names=["role"])
    return _to_user(account)
