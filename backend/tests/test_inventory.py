import pytest
import os
import json
import tempfile
from backend.services.inventory import InventoryService


@pytest.fixture
def temp_stock():
    data = [
        {"name": "Paneer", "qty": 1.4, "unit": "kg", "par": 0.5},
        {"name": "Chicken", "qty": 0, "unit": "kg", "par": 1.0},
        {"name": "Cashews", "qty": 300, "unit": "g", "par": 250},
        {"name": "Bay Leaves", "qty": 40, "unit": "g", "par": 10},
    ]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(data, f)
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_get_all(temp_stock):
    inv = InventoryService(temp_stock)
    items = inv.get_all()
    assert len(items) == 4
    paneer = next(i for i in items if i["name"] == "Paneer")
    assert paneer["is_below_par"] is False
    chicken = next(i for i in items if i["name"] == "Chicken")
    assert chicken["is_below_par"] is True


def test_add_item(temp_stock):
    inv = InventoryService(temp_stock)
    item = inv.add_item({"name": "Cardamom", "qty": 50, "unit": "g", "par": 10})
    assert item["name"] == "Cardamom"
    assert len(inv.get_all()) == 5


def test_add_duplicate_fails(temp_stock):
    inv = InventoryService(temp_stock)
    with pytest.raises(ValueError):
        inv.add_item({"name": "paneer", "qty": 1, "unit": "kg", "par": 0.5})


def test_update_item(temp_stock):
    inv = InventoryService(temp_stock)
    updated = inv.update_item("Chicken", {"qty": 5.0})
    assert updated["qty"] == 5.0
    assert updated["is_below_par"] is False


def test_delete_item(temp_stock):
    inv = InventoryService(temp_stock)
    deleted = inv.delete_item("Bay Leaves")
    assert deleted["name"] == "Bay Leaves"
    assert inv.get_item("Bay Leaves") is None


def test_deduct_stock(temp_stock):
    inv = InventoryService(temp_stock)
    updated = inv.deduct("Paneer", 180, "g")
    assert updated["qty"] == 1.22
