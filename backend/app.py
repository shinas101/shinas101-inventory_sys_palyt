import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from backend.services.inventory import InventoryService
from backend.services.menu import MenuService
from backend.services.orders import OrderService

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

inventory_service = InventoryService()
menu_service = MenuService()


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    try:
        items = inventory_service.get_all()
        for item in items:
            item["used_in_dishes"] = menu_service.get_dishes_using_ingredient(item["name"])
        return jsonify({"success": True, "data": items}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/inventory", methods=["POST"])
def add_ingredient():
    try:
        payload = request.get_json() or {}
        new_item = inventory_service.add_item(payload)
        new_item["used_in_dishes"] = menu_service.get_dishes_using_ingredient(new_item["name"])
        return jsonify({"success": True, "data": new_item}), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/inventory/<string:name>", methods=["PUT"])
def update_ingredient(name):
    try:
        payload = request.get_json() or {}
        updated = inventory_service.update_item(name, payload)
        updated["used_in_dishes"] = menu_service.get_dishes_using_ingredient(updated["name"])
        return jsonify({"success": True, "data": updated}), 200
    except KeyError as e:
        return jsonify({"success": False, "error": str(e).strip("'")}), 404
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/inventory/<string:name>", methods=["DELETE"])
def delete_ingredient(name):
    try:
        affected = menu_service.get_dishes_using_ingredient(name)
        deleted = inventory_service.delete_item(name)
        return jsonify({"success": True, "data": deleted, "affected_dishes": affected}), 200
    except KeyError as e:
        return jsonify({"success": False, "error": str(e).strip("'")}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/inventory/<string:name>/impact", methods=["GET"])
def ingredient_impact(name):
    affected = menu_service.get_dishes_using_ingredient(name)
    item = inventory_service.get_item(name)
    return jsonify({
        "success": True,
        "ingredient": name,
        "exists_in_stock": item is not None,
        "dependent_dishes": affected
    }), 200


@app.route("/api/menu", methods=["GET"])
def get_menu():
    try:
        menu = menu_service.get_menu(inventory_service)
        return jsonify({"success": True, "data": menu}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/orders", methods=["POST"])
def place_order():
    try:
        payload = request.get_json() or {}
        dish = payload.get("dish")
        servings = int(payload.get("servings", 1))
        order = OrderService.create_order(dish, servings, inventory_service, menu_service)
        return jsonify({"success": True, "data": order}), 200
    except KeyError as e:
        return jsonify({"success": False, "error": str(e).strip("'")}), 404
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset_stock():
    try:
        stock = inventory_service.reset()
        menu = menu_service.get_menu(inventory_service)
        return jsonify({"success": True, "inventory": stock, "menu": menu}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
