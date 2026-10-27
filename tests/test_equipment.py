async def test_list_equipment_sorted(client):
    res = await client.get("/api/equipment")
    assert res.status_code == 200
    items = res.json()
    names = [item["name"] for item in items]
    assert names == sorted(names)
    assert "Компрессор ВК-25" in names
    assert "Насос ЦНС 60-99" in names
    for item in items:
        assert item["id"] > 0
