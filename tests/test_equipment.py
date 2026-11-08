from tests.helpers import EMPLOYEE, login


async def test_equipment_requires_auth(client):
    assert (await client.get("/api/equipment")).status_code == 401


async def test_list_equipment_sorted_with_department(client):
    res = await client.get("/api/equipment", headers=await login(client, EMPLOYEE))
    assert res.status_code == 200
    items = res.json()
    names = [item["name"] for item in items]
    assert names == sorted(names)
    by_name = {item["name"]: item for item in items}
    assert by_name["Компрессор ВК-25"]["department"] == "Цех №2"
    assert by_name["Насос ЦНС 60-99"]["department"] == "Цех №4"
    assert all(item["id"] > 0 for item in items)
