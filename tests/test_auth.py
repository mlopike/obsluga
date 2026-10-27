EMPLOYEE = "ivanov@test.ru"
ENGINEER = "kuznetsova@test.ru"


async def login(client, email, password="secret123"):
    res = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["token"]


async def test_register_success(client):
    res = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Петров Пётр",
            "email": "petrov@test.ru",
            "department": "Цех №2",
            "role": "Сотрудник",
            "password": "secret123",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["token"]
    profile = body["profile"]
    assert profile["full_name"] == "Петров Пётр"
    assert profile["role"] == "Сотрудник"
    assert profile["department"] == "Цех №2"
    assert profile["id"] > 0


async def test_register_unknown_role(client):
    res = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Петров Пётр",
            "email": "petrov@test.ru",
            "department": "Цех №2",
            "role": "Мерл",
            "password": "secret123",
        },
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "Сотрудник" in detail and "Инженер" in detail


async def test_register_unknown_department(client):
    res = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Петров Пётр",
            "email": "petrov@test.ru",
            "department": "Цех №99",
            "role": "Сотрудник",
            "password": "secret123",
        },
    )
    assert res.status_code == 400
    assert "Цех №2" in res.json()["detail"]


async def test_register_duplicate_email(client):
    res = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Двойник",
            "email": EMPLOYEE,
            "department": "Цех №2",
            "role": "Сотрудник",
            "password": "secret123",
        },
    )
    assert res.status_code == 409


async def test_register_password_without_digit(client):
    res = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Петров Пётр",
            "email": "petrov@test.ru",
            "department": "Цех №2",
            "role": "Сотрудник",
            "password": "nodigits",
        },
    )
    assert res.status_code == 422


async def test_login_success(client):
    token = await login(client, EMPLOYEE)
    assert token


async def test_login_wrong_password(client):
    res = await client.post(
        "/api/auth/login", json={"email": EMPLOYEE, "password": "wrong9999"}
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Неверный email или пароль"


async def test_login_unknown_email(client):
    res = await client.post(
        "/api/auth/login", json={"email": "nobody@test.ru", "password": "secret123"}
    )
    assert res.status_code == 401


async def test_me(client):
    token = await login(client, ENGINEER)
    res = await client.get("/api/auth/me", headers={"Authorization": "Bearer " + token})
    assert res.status_code == 200
    profile = res.json()
    assert profile["full_name"] == "Кузнецова Мария"
    assert profile["role"] == "Инженер"
    assert profile["department"] == "Цех №2"


async def test_me_without_token(client):
    res = await client.get("/api/auth/me")
    assert res.status_code == 401
