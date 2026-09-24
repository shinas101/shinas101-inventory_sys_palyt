import pytest
from backend.app import app, inventory_service


@pytest.fixture
def client():
    app.config["TESTING"] = True
    inventory_service.reset()
    with app.test_client() as c:
        yield c


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json["status"] == "healthy"


def test_inventory_crud(client):
    res = client.get("/api/inventory")
    assert res.status_code == 200
    assert res.json["success"] is True

    # Add
    res = client.post("/api/inventory", json={"name": "Chili Powder", "qty": 100, "unit": "g", "par": 20})
    assert res.status_code == 201
    assert res.json["data"]["name"] == "Chili Powder"

    # Update
    res = client.put("/api/inventory/Chili Powder", json={"qty": 150})
    assert res.status_code == 200
    assert res.json["data"]["qty"] == 150

    # Delete
    res = client.delete("/api/inventory/Chili Powder")
    assert res.status_code == 200


def test_menu_endpoint(client):
    res = client.get("/api/menu")
    assert res.status_code == 200
    assert res.json["success"] is True


def test_order_endpoint(client):
    res = client.post("/api/orders", json={"dish": "Paneer Butter Masala", "servings": 1})
    assert res.status_code == 200
    assert res.json["success"] is True
