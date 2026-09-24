import uuid
from backend.services.units import convert_units


class OrderService:
    @staticmethod
    def create_order(dish_name, servings, inventory_service, menu_service):
        if not dish_name or not isinstance(dish_name, str):
            raise ValueError("Dish name is required")

        if not isinstance(servings, int) or servings < 1:
            raise ValueError("Servings must be at least 1")

        recipe = menu_service.get_dish(dish_name)
        if not recipe:
            raise KeyError(f"Dish '{dish_name}' not found")

        availability = menu_service.check_availability(recipe, inventory_service)
        if not availability["is_available"]:
            reasons_str = "; ".join(availability["unavailable_reasons"])
            raise ValueError(f"Dish is unavailable: {reasons_str}")

        # Check all ingredients for the required servings
        deductions_plan = []
        for ing in recipe.get("ingredients", []):
            ing_name = ing["name"]
            total_req_qty = ing["qty"] * servings
            req_unit = ing["unit"]

            stock_item = inventory_service.get_item(ing_name)
            if not stock_item:
                raise ValueError(f"Missing ingredient '{ing_name}' in stock")

            needed_in_stock_unit = convert_units(total_req_qty, req_unit, stock_item["unit"])
            if stock_item["qty"] < needed_in_stock_unit:
                raise ValueError(
                    f"Not enough '{ing_name}' for {servings} serving(s): "
                    f"needs {needed_in_stock_unit} {stock_item['unit']}, "
                    f"available {stock_item['qty']} {stock_item['unit']}"
                )

            deductions_plan.append({
                "name": ing_name,
                "amount": total_req_qty,
                "unit": req_unit,
                "stock_unit": stock_item["unit"],
                "stock_amount": needed_in_stock_unit,
            })

        # Apply stock deductions
        deductions_done = []
        for plan in deductions_plan:
            updated = inventory_service.deduct(plan["name"], plan["amount"], plan["unit"])
            deductions_done.append({
                "ingredient": plan["name"],
                "deducted": f"{plan['amount']} {plan['unit']}",
                "deducted_in_stock_unit": f"{plan['stock_amount']} {plan['stock_unit']}",
                "new_stock": f"{updated['qty']} {updated['unit']}",
                "is_below_par": updated["is_below_par"],
            })

        updated_menu = menu_service.get_menu(inventory_service)
        updated_stock = inventory_service.get_all()

        return {
            "order_id": f"ORD-{uuid.uuid4().hex[:6].upper()}",
            "dish": recipe["dish"],
            "servings": servings,
            "total_price": recipe.get("price", 0) * servings,
            "deductions": deductions_done,
            "updated_menu": updated_menu,
            "updated_inventory": updated_stock,
        }
