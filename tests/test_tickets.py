from tests.helpers import (
    ADMIN, EMPLOYEE, EMPLOYEE2, ENGINEER, ENGINEER2, create_ticket, login, profile,
)


def ids(res):
    return [t["id"] for t in res.json()]


# ---------- создание и видимость
async def test_list_requires_auth(client):
    assert (await client.get("/api/tickets")).status_code == 401


async def test_create_ticket_fields(client):
    emp = await login(client, EMPLOYEE)
    t = await create_ticket(client, emp)
    assert t["reporter"] == "Иванов Иван"
    assert t["reporter_department"] == "Цех №2"
    assert t["department"] == "Цех №2"  # цех оборудования
    assert t["engineer"] is None and t["engineer_id"] is None
    assert t["status"] == "new"
    assert t["equipment"] == "Компрессор ВК-25"
    assert t["diagnosis"] is None and t["workDone"] is None
    assert t["updated"]


async def test_ticket_department_is_equipment_department(client):
    emp = await login(client, EMPLOYEE)
    t = await create_ticket(client, emp, equipment_id=2)
    assert t["department"] == "Цех №4"
    assert t["reporter_department"] == "Цех №2"


async def test_only_employee_creates(client):
    for email in (ENGINEER, ADMIN):
        h = await login(client, email)
        res = await client.post("/api/tickets", json={"equipment_id": 1, "description": "x"}, headers=h)
        assert res.status_code == 403
    res = await client.post("/api/tickets", json={"equipment_id": 1, "description": "x"})
    assert res.status_code == 401


async def test_create_unknown_equipment(client):
    emp = await login(client, EMPLOYEE)
    res = await client.post("/api/tickets", json={"equipment_id": 9999, "description": "x"}, headers=emp)
    assert res.status_code == 404


async def test_employee_sees_only_own(client):
    e1 = await login(client, EMPLOYEE)
    e2 = await login(client, EMPLOYEE2)
    mine = await create_ticket(client, e1)
    other = await create_ticket(client, e2)
    got = ids(await client.get("/api/tickets", headers=e1))
    assert mine["id"] in got and other["id"] not in got


async def test_engineer_sees_queue_and_own_only(client):
    emp = await login(client, EMPLOYEE)
    e1 = await login(client, ENGINEER)
    e2 = await login(client, ENGINEER2)
    queued = await create_ticket(client, emp, description="в очереди")
    taken = await create_ticket(client, emp, description="возьмёт первый")
    assert (await client.post(f"/api/tickets/{taken['id']}/take", headers=e1)).status_code == 200

    seen1 = ids(await client.get("/api/tickets", headers=e1))
    seen2 = ids(await client.get("/api/tickets", headers=e2))
    assert queued["id"] in seen1 and taken["id"] in seen1
    assert queued["id"] in seen2 and taken["id"] not in seen2  # чужая в работе не видна


async def test_admin_sees_all(client):
    e1 = await login(client, EMPLOYEE)
    e2 = await login(client, EMPLOYEE2)
    adm = await login(client, ADMIN)
    a = await create_ticket(client, e1)
    b = await create_ticket(client, e2)
    got = ids(await client.get("/api/tickets", headers=adm))
    assert a["id"] in got and b["id"] in got


async def test_list_sorted_by_updated_desc(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    first = await create_ticket(client, emp, description="Первая")
    second = await create_ticket(client, emp, description="Вторая")
    order = ids(await client.get("/api/tickets", headers=emp))
    assert order.index(second["id"]) < order.index(first["id"])
    await client.post(f"/api/tickets/{first['id']}/take", headers=eng)
    order = ids(await client.get("/api/tickets", headers=emp))
    assert order.index(first["id"]) < order.index(second["id"])


# ---------- работа инженера
async def test_take_sets_engineer_and_progress(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    t = await create_ticket(client, emp)
    res = await client.post(f"/api/tickets/{t['id']}/take", headers=eng)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "progress"
    assert body["engineer"] == "Кузнецова Мария"
    assert body["engineer_id"] == (await profile(client, eng))["id"]


async def test_take_only_engineer(client):
    emp = await login(client, EMPLOYEE)
    t = await create_ticket(client, emp)
    for email in (EMPLOYEE, ADMIN):
        res = await client.post(f"/api/tickets/{t['id']}/take", headers=await login(client, email))
        assert res.status_code == 403


async def test_take_twice_conflict(client):
    emp = await login(client, EMPLOYEE)
    e1 = await login(client, ENGINEER)
    e2 = await login(client, ENGINEER2)
    t = await create_ticket(client, emp)
    assert (await client.post(f"/api/tickets/{t['id']}/take", headers=e1)).status_code == 200
    assert (await client.post(f"/api/tickets/{t['id']}/take", headers=e2)).status_code == 409


async def test_take_unknown(client):
    eng = await login(client, ENGINEER)
    assert (await client.post("/api/tickets/999999/take", headers=eng)).status_code == 404


async def test_patch_diagnosis_then_close(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    t = await create_ticket(client, emp)
    await client.post(f"/api/tickets/{t['id']}/take", headers=eng)

    res = await client.patch(
        f"/api/tickets/{t['id']}", json={"diagnosis": "Износ прокладки"}, headers=eng
    )
    assert res.status_code == 200 and res.json()["status"] == "progress"

    res = await client.patch(
        f"/api/tickets/{t['id']}",
        json={"status": "closed", "workDone": "Заменено уплотнение"},
        headers=eng,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "closed"
    assert body["diagnosis"] == "Износ прокладки"
    assert body["workDone"] == "Заменено уплотнение"


async def test_close_requires_diagnosis_and_work(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    t = await create_ticket(client, emp)
    await client.post(f"/api/tickets/{t['id']}/take", headers=eng)
    res = await client.patch(f"/api/tickets/{t['id']}", json={"status": "closed"}, headers=eng)
    assert res.status_code == 400
    res = await client.patch(
        f"/api/tickets/{t['id']}", json={"status": "closed", "diagnosis": "x"}, headers=eng
    )
    assert res.status_code == 400


async def test_patch_other_engineers_ticket_forbidden(client):
    emp = await login(client, EMPLOYEE)
    e1 = await login(client, ENGINEER)
    e2 = await login(client, ENGINEER2)
    t = await create_ticket(client, emp)
    await client.post(f"/api/tickets/{t['id']}/take", headers=e1)
    res = await client.patch(f"/api/tickets/{t['id']}", json={"diagnosis": "чужой"}, headers=e2)
    assert res.status_code == 403


async def test_patch_untaken_ticket_conflict(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    t = await create_ticket(client, emp)
    res = await client.patch(f"/api/tickets/{t['id']}", json={"diagnosis": "рано"}, headers=eng)
    assert res.status_code == 409


async def test_patch_forbidden_for_employee_and_admin(client):
    emp = await login(client, EMPLOYEE)
    t = await create_ticket(client, emp)
    for email in (EMPLOYEE, ADMIN):
        res = await client.patch(
            f"/api/tickets/{t['id']}", json={"diagnosis": "x"}, headers=await login(client, email)
        )
        assert res.status_code == 403


async def test_cannot_revert_to_new(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    t = await create_ticket(client, emp)
    await client.post(f"/api/tickets/{t['id']}/take", headers=eng)
    res = await client.patch(f"/api/tickets/{t['id']}", json={"status": "new"}, headers=eng)
    assert res.status_code == 400


async def test_closed_ticket_is_immutable(client):
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    adm = await login(client, ADMIN)
    t = await create_ticket(client, emp)
    await client.post(f"/api/tickets/{t['id']}/take", headers=eng)
    await client.patch(
        f"/api/tickets/{t['id']}",
        json={"status": "closed", "diagnosis": "d", "workDone": "w"},
        headers=eng,
    )
    assert (await client.patch(f"/api/tickets/{t['id']}", json={"diagnosis": "z"}, headers=eng)).status_code == 409
    eid = (await profile(client, await login(client, ENGINEER2)))["id"]
    assert (await client.post(f"/api/tickets/{t['id']}/assign", json={"engineer_id": eid}, headers=adm)).status_code == 409


# ---------- назначение админом
async def test_admin_assigns_engineer(client):
    emp = await login(client, EMPLOYEE)
    adm = await login(client, ADMIN)
    eng2 = await login(client, ENGINEER2)
    t = await create_ticket(client, emp)
    eid = (await profile(client, eng2))["id"]

    res = await client.post(f"/api/tickets/{t['id']}/assign", json={"engineer_id": eid}, headers=adm)
    assert res.status_code == 200
    body = res.json()
    assert body["engineer"] == "Орлов Андрей" and body["status"] == "progress"

    # назначенный инженер теперь может работать с заявкой
    res = await client.patch(f"/api/tickets/{t['id']}", json={"diagnosis": "ok"}, headers=eng2)
    assert res.status_code == 200


async def test_admin_reassigns_in_progress_ticket(client):
    emp = await login(client, EMPLOYEE)
    adm = await login(client, ADMIN)
    e1 = await login(client, ENGINEER)
    e2 = await login(client, ENGINEER2)
    t = await create_ticket(client, emp)
    await client.post(f"/api/tickets/{t['id']}/take", headers=e1)
    eid2 = (await profile(client, e2))["id"]
    res = await client.post(f"/api/tickets/{t['id']}/assign", json={"engineer_id": eid2}, headers=adm)
    assert res.status_code == 200 and res.json()["engineer"] == "Орлов Андрей"


async def test_assign_only_admin(client):
    emp = await login(client, EMPLOYEE)
    t = await create_ticket(client, emp)
    eid = (await profile(client, await login(client, ENGINEER)))["id"]
    for email in (EMPLOYEE, ENGINEER):
        res = await client.post(
            f"/api/tickets/{t['id']}/assign", json={"engineer_id": eid}, headers=await login(client, email)
        )
        assert res.status_code == 403


async def test_assign_rejects_non_engineer_and_unknown(client):
    emp = await login(client, EMPLOYEE)
    adm = await login(client, ADMIN)
    t = await create_ticket(client, emp)
    employee_id = (await profile(client, emp))["id"]
    r = await client.post(f"/api/tickets/{t['id']}/assign", json={"engineer_id": employee_id}, headers=adm)
    assert r.status_code == 400
    r = await client.post(f"/api/tickets/{t['id']}/assign", json={"engineer_id": 99999}, headers=adm)
    assert r.status_code == 400
    r = await client.post("/api/tickets/999999/assign", json={"engineer_id": employee_id}, headers=adm)
    assert r.status_code == 404
