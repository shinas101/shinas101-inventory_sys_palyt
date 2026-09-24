import pytest
import os
import json
import tempfile
from backend.services.inventory import InventoryService
from backend.services.menu import MenuService
from backend.services.orders import OrderService


@pytest.fixture
def services():
    stock = [
        {"name": "Paneer", "qty": 1.4, "unit": "kg", "par": 0.5},
        {"name": "Cashews", "qty": 300, "unit": "g", "par": 250},
        {"name": "Butter", "qty": 500, "unit": "g", "par": 100},
    ]
    recipes = [
        {
            "dish": "Paneer Butter Masala",
            "price": 320,
            "ingredients": [
                {"name": "Paneer", "qty": 180, "unit": "g"},
                {"name": "Butter", "qty": 30, "unit": "g"},
                {"name": "Cashews", "qty": 15, "unit": "g"}
            ]
        }
    ]

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f_s:
        json.dump(stock, f_s)
        s_path = f_s.name

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f_r:
        json.dump(recipes, f_r)
        r_path = f_r.name

    inv = InventoryService(s_path)
    menu = MenuService(r_path)

    yield inv, menu

    for p in (s_path, r_path):
        if os.path.exists(p):
            os.remove(p)


def test_order_deduction(services):
    inv, menu = services
    order = OrderService.create_order("Paneer Butter Masala", 1, inv, menu)
    assert order["dish"] == "Paneer Butter Masala"
    assert order["total_price"] == 320

    paneer = inv.get_item("Paneer")
    assert paneer["qty"] == 1.22


def test_order_crossing_par_level_makes_dish_unavailable(services):
    inv, menu = services
    # 4 servings use 60g Cashews -> 300 - 60 = 240g < 250g par
    order = OrderService.create_order("Paneer Butter Masala", 4, inv, menu)
    cashews = inv.get_item("Cashews")
    assert cashews["qty"] == 240.0
    assert cashews["is_below_par"] is True

    pbm = next(d for d in order["updated_menu"] if d["dish"] == "Paneer Butter Masala")
    assert pbm["is_available"] is False
