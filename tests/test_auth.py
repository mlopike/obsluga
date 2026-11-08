from tests.helpers import ADMIN, ENGINEER, EMPLOYEE, login, profile

REG = {
    "full_name": "Петров Пётр",
    "email": "petrov@test.ru",
    "department": "Цех №2",
    "password": "secret123",
}


async def test_register_success_creates_employee(client):
    res = await client.post("/api/auth/register", json=REG)
    assert res.status_code == 201
    body = res.json()
    assert body["token"]
    p = body["profile"]
    assert p["full_name"] == "Петров Пётр"
    assert p["role"] == "Сотрудник"
    assert p["perm"] == 1
    assert p["department"] == "Цех №2"


async def test_register_ignores_requested_role(client):
    """Нельзя зарегистрироваться инженером или админом, даже подставив role в тело."""
    for role in ("Инженер", "Администратор"):
        res = await client.post(
            "/api/auth/register", json={**REG, "email": f"{role}@test.ru", "role": role}
        )
        assert res.status_code == 201
        assert res.json()["profile"]["role"] == "Сотрудник"


async def test_register_unknown_department(client):
    res = await client.post("/api/auth/register", json={**REG, "department": "Цех №99"})
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "Цех №2" in detail and "Администрация" not in detail


async def test_register_admin_department_forbidden(client):
    res = await client.post("/api/auth/register", json={**REG, "department": "Администрация"})
    assert res.status_code == 400


async def test_register_duplicate_email(client):
    res = await client.post("/api/auth/register", json={**REG, "email": EMPLOYEE})
    assert res.status_code == 409


async def test_register_password_without_digit(client):
    res = await client.post("/api/auth/register", json={**REG, "password": "nodigits"})
    assert res.status_code == 422


async def test_departments_public_and_hides_admin(client):
    res = await client.get("/api/auth/departments")
    assert res.status_code == 200
    names = [d["name"] for d in res.json()]
    assert names == sorted(names)
    assert "Цех №2" in names and "Цех №4" in names
    assert "Администрация" not in names


async def test_login_success(client):
    assert await login(client, EMPLOYEE)


async def test_login_wrong_password(client):
    res = await client.post("/api/auth/login", json={"email": EMPLOYEE, "password": "wrong9999"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Неверный email или пароль"


async def test_login_unknown_email(client):
    res = await client.post("/api/auth/login", json={"email": "nobody@test.ru", "password": "secret123"})
    assert res.status_code == 401


async def test_me_for_each_role(client):
    eng = await profile(client, await login(client, ENGINEER))
    assert (eng["role"], eng["perm"], eng["department"]) == ("Инженер", 2, "Цех №2")
    adm = await profile(client, await login(client, ADMIN))
    assert (adm["role"], adm["perm"]) == ("Администратор", 3)


async def test_me_without_token(client):
    assert (await client.get("/api/auth/me")).status_code == 401
