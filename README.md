# Obsluga

Сервис регистрации заявок на устранение неисправностей оборудования (учебный проект).

Маршрут заявки: сотрудник регистрирует заявку по единице оборудования → инженер берёт её в работу, фиксирует диагноз и выполненные работы → заявка закрывается.

## Стек

- Python 3.10+, FastAPI, SQLAlchemy 2.0 (async, `Mapped`), PostgreSQL + asyncpg
- Alembic (async-миграции)
- bcrypt + PyJWT (JWT HS256)
- pydantic v2, pydantic-settings
- Фронтенд — статичные HTML/CSS/JS, отдаёт то же приложение (`StaticFiles` на `/` после роутеров `/api`)

## Структура

```
app/
  main.py          # FastAPI-приложение: роутеры /api + StaticFiles
  config.py        # Settings из app/.env
  database.py      # async engine, sessionmaker, Base
  models/          # department, equipment, role, account, request
  core/
    security.py    # bcrypt-хеши, создание/декодирование JWT
    deps.py        # get_current_account, require_roles, get_db
  schemas/         # pydantic-схемы: auth, equipment, request
  routers/         # auth, equipment, tickets
  seed.py          # идемпотентный сид
alembic/           # миграции
static/            # лендинг, login.html, tickets.html, admin.html, js/, css/
tests/             # pytest + httpx
docs/              # диаграмма схемы БД
```

## Запуск

1. PostgreSQL должен работать; база `obsluga` и пользователь созданы.
2. Виртуальное окружение и зависимости:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Заполнить `app/.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:5432/obsluga
   JWT_SECRET=<любая длинная секретная строка>
   TOKEN_HOURS=12
   TOKEN_HOURS_REMEMBER=720
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=<пароль первого администратора, от 8 символов>
   ```
4. Применить миграции:
   ```
   python -m alembic upgrade head
   ```
5. Посеять справочные данные (роли, цеха, 7 единиц оборудования) и создать первого администратора из `ADMIN_EMAIL`/`ADMIN_PASSWORD` (идемпотентно, существующий аккаунт не меняется):
   ```
   python -m app.seed
   ```
6. Запустить приложение:
   ```
   uvicorn app.main:app --reload
   ```

## Роли

| Роль | Страница | Что можно |
|------|----------|-----------|
| Сотрудник (по умолчанию при регистрации) | `tickets.html` | подавать заявки, видеть только свои |
| Инженер (назначает администратор) | `tickets.html` | видеть очередь новых и свои заявки, брать в работу, фиксировать диагноз и работы, закрывать |
| Администратор (создаётся сидом) | `admin.html` | видеть все заявки, назначать и переназначать инженера, менять роль Сотрудник ⇄ Инженер |

Права проверяются на сервере (`403`), перенаправления на страницах — только удобство.

API: `POST /api/tickets/{id}/take` (инженер), `PATCH /api/tickets/{id}` (инженер, своя заявка),
`POST /api/tickets/{id}/assign` (админ), `GET /api/users`, `PATCH /api/users/{id}` (админ),
`GET /api/auth/departments` (публичный список цехов для регистрации).


- `http://127.0.0.1:8000/` — лендинг
- `http://127.0.0.1:8000/login.html` — вход и регистрация
- `http://127.0.0.1:8000/tickets.html` — кабинет сотрудника и инженера
- `http://127.0.0.1:8000/admin.html` — панель администратора
- `http://127.0.0.1:8000/docs` — Swagger

## Тесты

```
pytest
```

Тесты ходят в базу из `app/.env` и между тестами сбрасывают данные таблиц (TRUNCATE), поэтому после прогона рекомендуется заново выполнить `python -m app.seed`.

## CI

GitHub Actions (`.github/workflows/ci.yml`): проверка моделей + `pytest` на чистом PostgreSQL 16.

## Документация

- `TODO.ipynb` — спецификация бэкенда и план по фазам.
- `docs/db_schema.svg` — диаграмма схемы базы данных.
