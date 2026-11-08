from tests.helpers import ADMIN, EMPLOYEE, ENGINEER, ENGINEER2, create_ticket, login, profile


async def users(client, headers, **params):
    res = await client.get("/api/users", headers=headers, params=params)
    assert res.status_code == 200
    return res.json()


async def test_users_admin_only(client):
    assert (await client.get("/api/users")).status_code == 401
    for email in (EMPLOYEE, ENGINEER):
        res = await client.get("/api/users", headers=await login(client, email))
        assert res.status_code == 403


async def test_list_users_and_filter_by_role(client):
    adm = await login(client, ADMIN)
    all_users = await users(client, adm)
    assert len(all_users) == 5
    assert all(set(u) == {"id", "full_name", "email", "role", "perm", "department"} for u in all_users)
    engineers = await users(client, adm, role="Инженер")
    assert {u["full_name"] for u in engineers} == {"Кузнецова Мария", "Орлов Андрей"}


async def test_admin_promotes_employee_to_engineer(client):
    adm = await login(client, ADMIN)
    emp = await login(client, EMPLOYEE)
    uid = (await profile(client, emp))["id"]
    res = await client.patch(f"/api/users/{uid}", json={"role": "Инженер"}, headers=adm)
    assert res.status_code == 200
    assert res.json()["role"] == "Инженер" and res.json()["perm"] == 2
    # новая роль действует сразу: теперь это инженер без права создавать заявки
    r = await client.post("/api/tickets", json={"equipment_id": 1, "description": "x"}, headers=emp)
    assert r.status_code == 403


async def test_cannot_set_admin_role_or_change_admin(client):
    adm = await login(client, ADMIN)
    emp_id = (await profile(client, await login(client, EMPLOYEE)))["id"]
    adm_id = (await profile(client, adm))["id"]
    r = await client.patch(f"/api/users/{emp_id}", json={"role": "Администратор"}, headers=adm)
    assert r.status_code == 400
    r = await client.patch(f"/api/users/{adm_id}", json={"role": "Сотрудник"}, headers=adm)
    assert r.status_code == 403


async def test_demote_engineer_blocked_with_open_tickets(client):
    adm = await login(client, ADMIN)
    emp = await login(client, EMPLOYEE)
    eng = await login(client, ENGINEER)
    eng_id = (await profile(client, eng))["id"]
    t = await create_ticket(client, emp)
    await client.post(f"/api/tickets/{t['id']}/take", headers=eng)

    r = await client.patch(f"/api/users/{eng_id}", json={"role": "Сотрудник"}, headers=adm)
    assert r.status_code == 409

    await client.patch(
        f"/api/tickets/{t['id']}",
        json={"status": "closed", "diagnosis": "d", "workDone": "w"},
        headers=eng,
    )
    r = await client.patch(f"/api/users/{eng_id}", json={"role": "Сотрудник"}, headers=adm)
    assert r.status_code == 200 and r.json()["role"] == "Сотрудник"


async def test_change_role_unknown_user(client):
    adm = await login(client, ADMIN)
    r = await client.patch("/api/users/99999", json={"role": "Инженер"}, headers=adm)
    assert r.status_code == 404
