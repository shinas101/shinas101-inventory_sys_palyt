import json
import os
import copy
from backend.services.units import convert_units

RECIPES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "recipes.json")


class MenuService:
    def __init__(self, file_path=None):
        self.file_path = file_path or RECIPES_FILE
        self.recipes = []
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.recipes = json.load(f)
        else:
            self.recipes = []

    def get_all(self):
        return copy.deepcopy(self.recipes)

    def get_dish(self, name):
        search_name = name.strip().lower()
        for recipe in self.recipes:
            if recipe["dish"].strip().lower() == search_name:
                return copy.deepcopy(recipe)
        return None

    def get_dishes_using_ingredient(self, ingredient_name):
        search_name = ingredient_name.strip().lower()
        dishes = []
        for recipe in self.recipes:
            for ing in recipe.get("ingredients", []):
                if ing["name"].strip().lower() == search_name:
                    dishes.append(recipe["dish"])
                    break
        return dishes

    def check_availability(self, recipe, inventory_service):
        dish_name = recipe["dish"]
        price = recipe.get("price", 0)
        is_available = True
        reasons = []
        ingredients_status = []

        for ing in recipe.get("ingredients", []):
            ing_name = ing["name"]
            req_qty = ing["qty"]
            req_unit = ing["unit"]

            stock_item = inventory_service.get_item(ing_name)

            if not stock_item:
                is_available = False
                msg = f"Missing ingredient in stock: '{ing_name}'"
                reasons.append(msg)
                ingredients_status.append({
                    "name": ing_name,
                    "required_qty": req_qty,
                    "required_unit": req_unit,
                    "stock_qty": None,
                    "stock_unit": None,
                    "par": None,
                    "status": "missing",
                    "reason": msg,
                })
                continue

            stock_qty = stock_item["qty"]
            stock_unit = stock_item["unit"]
            par = stock_item["par"]

            try:
                needed_in_stock_unit = convert_units(req_qty, req_unit, stock_unit)
            except ValueError as e:
                is_available = False
                msg = f"Unit error for '{ing_name}': {str(e)}"
                reasons.append(msg)
                ingredients_status.append({
                    "name": ing_name,
                    "required_qty": req_qty,
                    "required_unit": req_unit,
                    "stock_qty": stock_qty,
                    "stock_unit": stock_unit,
                    "par": par,
                    "status": "unit_error",
                    "reason": msg,
                })
                continue

            below_par = stock_qty < par
            below_portion = stock_qty < needed_in_stock_unit

            status = "ok"
            reason = None

            if below_par:
                is_available = False
                status = "below_par"
                reason = f"'{ing_name}' is below par ({stock_qty} {stock_unit} < {par} {stock_unit})"
                reasons.append(reason)
            elif below_portion:
                is_available = False
                status = "insufficient_stock"
                reason = f"'{ing_name}' has less than 1 portion in stock ({stock_qty} {stock_unit} < {needed_in_stock_unit} {stock_unit})"
                reasons.append(reason)

            ingredients_status.append({
                "name": ing_name,
                "required_qty": req_qty,
                "required_unit": req_unit,
                "required_in_stock_unit": needed_in_stock_unit,
                "stock_qty": stock_qty,
                "stock_unit": stock_unit,
                "par": par,
                "status": status,
                "reason": reason,
            })

        return {
            "dish": dish_name,
            "price": price,
            "is_available": is_available,
            "unavailable_reasons": reasons,
            "ingredients": ingredients_status,
        }

    def get_menu(self, inventory_service):
        result = []
        for recipe in self.recipes:
            result.append(self.check_availability(recipe, inventory_service))
        return result
