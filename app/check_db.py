import asyncio

import sqlalchemy as sa

from app.config import Settings
from app.database import engine

settings = Settings()


async def get_user():
    # 1. Печатаем сгенерированный URL (пароль будет скрыт звёздочками)
    print("🔗 Сгенерированный URL:", settings.db_url.render_as_string(hide_password=True))
    print(f"👤 Логин: {settings.db_user}")
    print(f"🌐 Хост: {settings.db_host}:{settings.db_port}")
    print(f"🗄️ База данных: {settings.db_name}")

    print("\n🔄 Пытаемся подключиться...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(sa.text("SELECT VERSION()"))
            print(f"✅ Успех! Версия БД: {result.scalar()}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(get_user())