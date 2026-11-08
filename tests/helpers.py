EMPLOYEE = "ivanov@test.ru"
EMPLOYEE2 = "sidorov@test.ru"
ENGINEER = "kuznetsova@test.ru"
ENGINEER2 = "orlov@test.ru"
ADMIN = "admin@test.ru"


async def login(client, email, password="secret123"):
    res = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": "Bearer " + res.json()["token"]}


async def profile(client, headers):
    return (await client.get("/api/auth/me", headers=headers)).json()


async def create_ticket(client, headers, description="Слабое нагнетание", equipment_id=1):
    res = await client.post(
        "/api/tickets", json={"equipment_id": equipment_id, "description": description}, headers=headers
    )
    assert res.status_code == 201, res.text
    return res.json()
