from fastapi.testclient import TestClient

from schemas.enums import Category


def test_list_products_empty(client: TestClient) -> None:
    response = client.get("/products/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_create_product(client: TestClient) -> None:
    payload = {
        "sku": "ELEC-001",
        "name": "Laptop",
        "category": Category.ELECTRONICS,
        "stock_qty": 50,
        "reorder_level": 10,
    }
    response = client.post("/products/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "ELEC-001"
    assert data["name"] == "Laptop"
    assert data["category"] == Category.ELECTRONICS
    assert "id" in data
    assert "updated_at" in data


def test_get_product_by_id(client: TestClient) -> None:
    payload = {"sku": "OFF-001", "name": "Desk Chair", "category": Category.OFFICE, "stock_qty": 20, "reorder_level": 5}
    created = client.post("/products/", json=payload).json()

    response = client.get(f"/products/{created['id']}")
    assert response.status_code == 200
    assert response.json()["sku"] == "OFF-001"


def test_get_product_not_found(client: TestClient) -> None:
    response = client.get("/products/99999")
    assert response.status_code == 404


def test_filter_products_by_category(client: TestClient) -> None:
    client.post(
        "/products/",
        json={
            "sku": "SUP-001",
            "name": "Stapler",
            "category": Category.SUPPLIES,
            "stock_qty": 100,
            "reorder_level": 20,
        },
    )
    client.post(
        "/products/",
        json={
            "sku": "ELEC-002",
            "name": "Monitor",
            "category": Category.ELECTRONICS,
            "stock_qty": 15,
            "reorder_level": 3,
        },
    )

    response = client.get("/products/?category=Supplies")
    assert response.status_code == 200
    results = response.json()["items"]
    assert all(p["category"] == Category.SUPPLIES for p in results)
