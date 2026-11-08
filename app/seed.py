"""Идемпотентный сид: роли, цеха, оборудование. Запуск: python -m app.seed"""
import asyncio

from sqlalchemy import select

from app.core.roles import ADMIN_DEPARTMENT, ROLE_ADMIN, ROLE_ENGINEER, ROLE_EMPLOYEE, PERM_ADMIN, PERM_ENGINEER, PERM_EMPLOYEE
from app.core.security import hash_password, settings
from app.database import async_session, engine
from app.models.account import Account
from app.models.department import Department
from app.models.equipment import Equipment
from app.models.role import Role

ROLES = [
    (ROLE_EMPLOYEE, PERM_EMPLOYEE),
    (ROLE_ENGINEER, PERM_ENGINEER),
    (ROLE_ADMIN, PERM_ADMIN),
]

DEPARTMENTS = ["Цех №1", "Цех №2", "Цех №3", "Цех №4"]

EQUIPMENT = [
    ("Токарный станок 16К20", "Цех №1"),
    ("Компрессор ВК-25", "Цех №2"),
    ("Конвейерная лента №3", "Цех №3"),
    ("Сварочный аппарат ТДМ-317", "Цех №2"),
    ("Насос ЦНС 60-99", "Цех №4"),
    ("Пресс гидравлический ПГ-100", "Цех №1"),
    ("Электропогрузчик EP-16", "Цех №3"),
]


async def get_or_create_role(session, name: str, perm_level: int) -> Role:
    role = (await session.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
    if role is None:
        role = Role(name=name, perm_level=perm_level)
        session.add(role)
        await session.flush()
    return role


async def get_or_create_department(session, name: str) -> Department:
    department = (await session.execute(select(Department).where(Department.name == name))).scalar_one_or_none()
    if department is None:
        department = Department(name=name)
        session.add(department)
        await session.flush()
    return department


async def get_or_create_equipment(session, name: str, department: Department) -> Equipment:
    equipment = (await session.execute(select(Equipment).where(Equipment.name == name))).scalar_one_or_none()
    if equipment is None:
        equipment = Equipment(name=name, department=department)
        session.add(equipment)
        await session.flush()
    return equipment


async def ensure_admin(session) -> bool:
    """Создаёт первого администратора из ADMIN_EMAIL / ADMIN_PASSWORD (.env). Пароль существующего не трогает."""
    if not settings.admin_email or not settings.admin_password:
        return False
    existing = (await session.execute(select(Account).where(Account.email == settings.admin_email))).scalar_one_or_none()
    if existing is not None:
        return False
    role = await get_or_create_role(session, ROLE_ADMIN, PERM_ADMIN)
    department = await get_or_create_department(session, ADMIN_DEPARTMENT)
    session.add(
        Account(
            full_name=settings.admin_full_name,
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role_id=role.role_id,
            department_id=department.department_id,
        )
    )
    return True


async def seed() -> None:
    try:
        async with async_session() as session:
            for name, perm_level in ROLES:
                await get_or_create_role(session, name, perm_level)
            for name in DEPARTMENTS:
                await get_or_create_department(session, name)
            for name, department_name in EQUIPMENT:
                department = await get_or_create_department(session, department_name)
                await get_or_create_equipment(session, name, department)
            admin_created = await ensure_admin(session)
            await session.commit()
        print(f"Сид выполнен: ролей={len(ROLES)}, цехов={len(DEPARTMENTS)}, единиц оборудования={len(EQUIPMENT)}")
        if admin_created:
            print(f"Создан администратор: {settings.admin_email}")
        elif not settings.admin_email or not settings.admin_password:
            print("Администратор не создан: задайте ADMIN_EMAIL и ADMIN_PASSWORD в app/.env и повторите сид")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
