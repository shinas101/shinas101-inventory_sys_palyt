import json
import os
import copy
from backend.services.units import normalize_unit, get_dimension, convert_units

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "stock.json")


class InventoryService:
    def __init__(self, file_path=None):
        self.file_path = file_path or DATA_FILE
        self.stock = []
        self.initial_stock = []
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.stock = json.load(f)
        else:
            self.stock = []
        if not self.initial_stock and self.stock:
            self.initial_stock = copy.deepcopy(self.stock)

    def save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.stock, f, indent=2)

    def reset(self):
        if self.initial_stock:
            self.stock = copy.deepcopy(self.initial_stock)
            self.save()
        return self.get_all()

    def get_all(self):
        result = []
        for item in self.stock:
            row = copy.deepcopy(item)
            row["is_below_par"] = row["qty"] < row["par"]
            result.append(row)
        return result

    def get_item(self, name):
        search_name = name.strip().lower()
        for item in self.stock:
            if item["name"].strip().lower() == search_name:
                row = copy.deepcopy(item)
                row["is_below_par"] = row["qty"] < row["par"]
                return row
        return None

    def validate(self, data, is_update=False):
        if not isinstance(data, dict):
            raise ValueError("Invalid request body")

        validated = {}

        if not is_update:
            if "name" not in data or not str(data["name"]).strip():
                raise ValueError("Ingredient name is required")
            name = str(data["name"]).strip()
            if self.get_item(name) is not None:
                raise ValueError(f"Ingredient '{name}' already exists")
            validated["name"] = name
        elif "name" in data:
            name = str(data["name"]).strip()
            if not name:
                raise ValueError("Ingredient name cannot be empty")
            validated["name"] = name

        if "qty" in data or not is_update:
            if "qty" not in data:
                raise ValueError("Quantity is required")
            try:
                qty = float(data["qty"])
            except (ValueError, TypeError):
                raise ValueError("Quantity must be a valid number")
            if qty < 0:
                raise ValueError("Quantity cannot be negative")
            validated["qty"] = round(qty, 4)

        if "unit" in data or not is_update:
            if "unit" not in data:
                raise ValueError("Unit is required")
            unit = normalize_unit(str(data["unit"]))
            if not unit:
                raise ValueError("Unit is required")
            get_dimension(unit)
            validated["unit"] = unit

        if "par" in data or not is_update:
            if "par" not in data:
                raise ValueError("Par level is required")
            try:
                par = float(data["par"])
            except (ValueError, TypeError):
                raise ValueError("Par level must be a valid number")
            if par < 0:
                raise ValueError("Par level cannot be negative")
            validated["par"] = round(par, 4)

        return validated

    def add_item(self, data):
        clean = self.validate(data, is_update=False)
        new_item = {
            "name": clean["name"],
            "qty": clean["qty"],
            "unit": clean["unit"],
            "par": clean["par"],
        }
        self.stock.append(new_item)
        self.save()
        return self.get_item(clean["name"])

    def update_item(self, name, data):
        target_name = name.strip().lower()
        idx = None
        for i, item in enumerate(self.stock):
            if item["name"].strip().lower() == target_name:
                idx = i
                break

        if idx is None:
            raise KeyError(f"Ingredient '{name}' not found")

        clean = self.validate(data, is_update=True)
        current = self.stock[idx]

        if "unit" in clean and clean["unit"] != current["unit"]:
            get_dimension(clean["unit"])
            current["unit"] = clean["unit"]

        if "name" in clean:
            current["name"] = clean["name"]
        if "qty" in clean:
            current["qty"] = clean["qty"]
        if "par" in clean:
            current["par"] = clean["par"]

        self.stock[idx] = current
        self.save()
        return self.get_item(current["name"])

    def delete_item(self, name):
        target_name = name.strip().lower()
        idx = None
        for i, item in enumerate(self.stock):
            if item["name"].strip().lower() == target_name:
                idx = i
                break

        if idx is None:
            raise KeyError(f"Ingredient '{name}' not found")

        removed = self.stock.pop(idx)
        self.save()
        return removed

    def deduct(self, name, required_qty, recipe_unit):
        target_name = name.strip().lower()
        idx = None
        for i, item in enumerate(self.stock):
            if item["name"].strip().lower() == target_name:
                idx = i
                break

        if idx is None:
            raise KeyError(f"Ingredient '{name}' not in stock")

        stock_item = self.stock[idx]
        needed_in_stock_unit = convert_units(required_qty, recipe_unit, stock_item["unit"])

        if stock_item["qty"] < needed_in_stock_unit:
            raise ValueError(
                f"Not enough stock for '{name}': needs {needed_in_stock_unit} {stock_item['unit']}, "
                f"only {stock_item['qty']} {stock_item['unit']} in stock"
            )

        stock_item["qty"] = round(stock_item["qty"] - needed_in_stock_unit, 4)
        self.stock[idx] = stock_item
        self.save()
        return self.get_item(stock_item["name"])
