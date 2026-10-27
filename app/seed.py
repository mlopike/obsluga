"""Идемпотентный сид: роли, цеха, оборудование. Запуск: python -m app.seed"""
import asyncio

from sqlalchemy import select

from app.database import async_session, engine
from app.models.department import Department
from app.models.equipment import Equipment
from app.models.role import Role

ROLES = [
    ("Сотрудник", 1),
    ("Инженер", 2),
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
            await session.commit()
        print(f"Сид выполнен: ролей={len(ROLES)}, цехов={len(DEPARTMENTS)}, единиц оборудования={len(EQUIPMENT)}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
