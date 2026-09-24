import pytest
import os
import json
import tempfile
from backend.services.inventory import InventoryService
from backend.services.menu import MenuService


@pytest.fixture
def services():
    stock = [
        {"name": "Paneer", "qty": 1.4, "unit": "kg", "par": 0.5},
        {"name": "Chicken", "qty": 0, "unit": "kg", "par": 1.0},
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
        },
        {
            "dish": "Chicken Biryani",
            "price": 420,
            "ingredients": [
                {"name": "Chicken", "qty": 250, "unit": "g"}
            ]
        },
        {
            "dish": "Jeera Rice",
            "price": 180,
            "ingredients": [
                {"name": "Cumin Seeds", "qty": 5, "unit": "g"}
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


def test_available_dish(services):
    inv, menu = services
    recipe = menu.get_dish("Paneer Butter Masala")
    res = menu.check_availability(recipe, inv)
    assert res["is_available"] is True


def test_unavailable_dish_below_par(services):
    inv, menu = services
    recipe = menu.get_dish("Chicken Biryani")
    res = menu.check_availability(recipe, inv)
    assert res["is_available"] is False


def test_unavailable_dish_missing_ingredient(services):
    inv, menu = services
    recipe = menu.get_dish("Jeera Rice")
    res = menu.check_availability(recipe, inv)
    assert res["is_available"] is False
    assert any("Missing ingredient" in r for r in res["unavailable_reasons"])
