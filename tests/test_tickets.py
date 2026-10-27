EMPLOYEE = "ivanov@test.ru"
ENGINEER = "kuznetsova@test.ru"


async def login(client, email, password="secret123"):
    res = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": "Bearer " + res.json()["token"]}


async def create_ticket(client, headers, description="Слабое нагнетание", equipment_id=1):
    res = await client.post(
        "/api/tickets", json={"equipment_id": equipment_id, "description": description}, headers=headers
    )
    assert res.status_code == 201
    return res.json()


async def test_create_requires_auth(client):
    res = await client.post(
        "/api/tickets", json={"equipment_id": 1, "description": "Слабое нагнетание"}
    )
    assert res.status_code == 401


async def test_create_ticket(client):
    headers = await login(client, EMPLOYEE)
    ticket = await create_ticket(client, headers)
    assert ticket["reporter"] == "Иванов Иван"
    assert ticket["engineer"] is None
    assert ticket["status"] == "new"
    assert ticket["equipment"] == "Компрессор ВК-25"
    assert ticket["description"] == "Слабое нагнетание"
    assert ticket["diagnosis"] is None
    assert ticket["workDone"] is None
    assert ticket["updated"]


async def test_list_contains_created(client):
    headers = await login(client, EMPLOYEE)
    ticket = await create_ticket(client, headers)
    res = await client.get("/api/tickets")
    assert res.status_code == 200
    assert any(item["id"] == ticket["id"] for item in res.json())


async def test_patch_forbidden_for_employee(client):
    emp = await login(client, EMPLOYEE)
    ticket = await create_ticket(client, emp)
    res = await client.patch(
        f"/api/tickets/{ticket['id']}", json={"status": "progress"}, headers=emp
    )
    assert res.status_code == 403


async def test_patch_unknown_ticket(client):
    eng = await login(client, ENGINEER)
    res = await client.patch("/api/tickets/999999", json={"status": "closed"}, headers=eng)
    assert res.status_code == 404


async def test_patch_progress_assigns_engineer(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    ticket = await create_ticket(client, emp)

    res = await client.patch(
        f"/api/tickets/{ticket['id']}", json={"status": "progress"}, headers=eng
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "progress"
    assert body["engineer"] == "Кузнецова Мария"


async def test_patch_workdone_alias_and_diagnosis(client):
    eng = await login(client, ENGINEER)
    ticket = await create_ticket(client, eng)

    res = await client.patch(
        f"/api/tickets/{ticket['id']}",
        json={"status": "closed", "diagnosis": "Износ прокладки", "workDone": "Заменено уплотнение"},
        headers=eng,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "closed"
    assert body["diagnosis"] == "Износ прокладки"
    assert body["workDone"] == "Заменено уплотнение"


async def test_list_sorted_by_updated_desc(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    first = await create_ticket(client, emp, description="Первая")
    second = await create_ticket(client, emp, description="Вторая")

    order = [item["id"] for item in (await client.get("/api/tickets")).json()]
    assert order.index(second["id"]) < order.index(first["id"])

    res = await client.patch(
        f"/api/tickets/{first['id']}", json={"status": "progress"}, headers=eng
    )
    assert res.status_code == 200

    order = [item["id"] for item in (await client.get("/api/tickets")).json()]
    assert order.index(first["id"]) < order.index(second["id"])
