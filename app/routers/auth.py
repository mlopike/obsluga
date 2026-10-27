from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.deps import CurrentAccount, DbSession
from app.core.security import create_token, hash_password, verify_password
from app.models.account import Account
from app.models.department import Department
from app.models.role import Role
from app.schemas.auth import LoginIn, ProfileOut, RegisterIn, TokenOut

router = APIRouter()


def _to_profile(account: Account) -> ProfileOut:
    return ProfileOut(
        id=account.account_id,
        full_name=account.full_name,
        role=account.role.name,
        department=account.department.name,
    )


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterIn, db: DbSession) -> TokenOut:
    role = (await db.execute(select(Role).where(Role.name == data.role))).scalar_one_or_none()
    if role is None:
        roles = [r[0] for r in (await db.execute(select(Role.name).order_by(Role.name)))]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неизвестная роль «{data.role}». Допустимые значения: {', '.join(roles)}",
        )
    department = (await db.execute(select(Department).where(Department.name == data.department))).scalar_one_or_none()
    if department is None:
        departments = [d[0] for d in (await db.execute(select(Department.name).order_by(Department.name)))]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неизвестный цех «{data.department}». Допустимые значения: {', '.join(departments)}",
        )
    existing = (await db.execute(select(Account).where(Account.email == data.email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    account = Account(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=role.role_id,
        department_id=department.department_id,
    )
    db.add(account)
    await db.commit()

    token = create_token(
        account.account_id,
        role.perm_level,
        department.department_id,
        account.full_name,
        remember=False,
    )
    return TokenOut(token=token, profile=_to_profile(account))


@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: DbSession) -> TokenOut:
    result = await db.execute(
        select(Account)
        .where(Account.email == data.email)
        .options(joinedload(Account.role), joinedload(Account.department))
    )
    account = result.scalar_one_or_none()
    if account is None or not verify_password(data.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    token = create_token(
        account.account_id,
        account.role.perm_level,
        account.department.department_id,
        account.full_name,
        remember=data.remember,
    )
    return TokenOut(token=token, profile=_to_profile(account))


@router.get("/me", response_model=ProfileOut)
async def me(current: CurrentAccount, db: DbSession) -> ProfileOut:
    result = await db.execute(
        select(Account)
        .where(Account.account_id == current.account_id)
        .options(joinedload(Account.role), joinedload(Account.department))
    )
    return _to_profile(result.scalar_one())
