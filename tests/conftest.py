import httpx
import pytest
from sqlalchemy import text

from app.core.security import hash_password
from app.database import Base, async_session, engine
from app.main import app
from app.models.account import Account
from app.models.department import Department
from app.models.equipment import Equipment
from app.models.role import Role


@pytest.fixture()
async def client():
    # Таблицы гарантированно существуют (в CI БД пустая), затем сброс данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("TRUNCATE request, equipment, account, department, role RESTART IDENTITY CASCADE")
        )

    role_employee = Role(name="Сотрудник", perm_level=1)
    role_engineer = Role(name="Инженер", perm_level=2)
    department = Department(name="Цех №2")
    compressor = Equipment(name="Компрессор ВК-25", department=department)
    pump = Equipment(name="Насос ЦНС 60-99", department=department)
    employee = Account(
        full_name="Иванов Иван",
        email="ivanov@test.ru",
        password_hash=hash_password("secret123"),
        role=role_employee,
        department=department,
    )
    engineer = Account(
        full_name="Кузнецова Мария",
        email="kuznetsova@test.ru",
        password_hash=hash_password("secret123"),
        role=role_engineer,
        department=department,
    )
    async with async_session() as session:
        session.add_all([role_employee, role_engineer, department, compressor, pump, employee, engineer])
        await session.commit()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Пул пушится, чтобы следующий тест (с другим event loop) подключился заново
    await engine.dispose()
