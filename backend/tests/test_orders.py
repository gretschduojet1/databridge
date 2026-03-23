from decimal import Decimal

from fastapi.testclient import TestClient

from schemas.enums import Category, Region


def _create_customer(client: TestClient, suffix: str = "") -> int:
    r = client.post(
        "/customers/",
        json={
            "name": f"Customer{suffix}",
            "email": f"c{suffix}@example.com",
            "region": Region.WEST,
        },
    )
    return r.json()["id"]


def _create_product(client: TestClient, suffix: str = "") -> int:
    r = client.post(
        "/products/",
        json={
            "sku": f"SKU-{suffix}",
            "name": f"Product{suffix}",
            "category": Category.OFFICE,
            "stock_qty": 100,
            "reorder_level": 10,
        },
    )
    return r.json()["id"]


def test_list_orders_empty(client: TestClient) -> None:
    response = client.get("/orders/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_create_order(client: TestClient) -> None:
    cid = _create_customer(client, "ord1")
    pid = _create_product(client, "ord1")

    payload = {"customer_id": cid, "product_id": pid, "quantity": 3, "unit_price": "9.99"}
    response = client.post("/orders/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 3
    assert Decimal(data["unit_price"]) == Decimal("9.99")
    assert "id" in data
    assert "ordered_at" in data


def test_get_order_by_id(client: TestClient) -> None:
    cid = _create_customer(client, "ord2")
    pid = _create_product(client, "ord2")
    created = client.post(
        "/orders/",
        json={"customer_id": cid, "product_id": pid, "quantity": 1, "unit_price": "19.99"},
    ).json()

    response = client.get(f"/orders/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_order_not_found(client: TestClient) -> None:
    response = client.get("/orders/99999")
    assert response.status_code == 404


def test_filter_orders_by_customer(client: TestClient) -> None:
    cid = _create_customer(client, "ord3")
    pid = _create_product(client, "ord3")
    client.post("/orders/", json={"customer_id": cid, "product_id": pid, "quantity": 2, "unit_price": "5.00"})

    response = client.get(f"/orders/?customer_id={cid}")
    assert response.status_code == 200
    results = response.json()["items"]
    assert all(o["customer_id"] == cid for o in results)
