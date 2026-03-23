from fastapi.testclient import TestClient

from schemas.enums import Category


def _make_product(client: TestClient, sku: str, stock: int, reorder: int) -> dict:
    return client.post(
        "/products/",
        json={
            "sku": sku,
            "name": f"Product {sku}",
            "category": Category.ELECTRONICS,
            "stock_qty": stock,
            "reorder_level": reorder,
        },
    ).json()


def test_stock_health_returns_ok(client: TestClient) -> None:
    response = client.get("/reports/inventory/stock-health")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stock_health_sorted_by_margin(client: TestClient) -> None:
    # margins: A=-5 (low stock), B=0 (at threshold), C=50 (healthy)
    _make_product(client, "A-001", stock=5, reorder=10)  # margin -5
    _make_product(client, "B-001", stock=10, reorder=10)  # margin 0
    _make_product(client, "C-001", stock=60, reorder=10)  # margin 50

    response = client.get("/reports/inventory/stock-health?limit=10")
    assert response.status_code == 200
    items = response.json()

    skus = [i["sku"] for i in items]
    assert skus.index("A-001") < skus.index("B-001") < skus.index("C-001")


def test_stock_health_is_low_stock_flag(client: TestClient) -> None:
    _make_product(client, "LOW-001", stock=3, reorder=10)
    _make_product(client, "OK-001", stock=20, reorder=10)

    items = client.get("/reports/inventory/stock-health?limit=10").json()
    by_sku = {i["sku"]: i for i in items}

    assert by_sku["LOW-001"]["is_low_stock"] is True
    assert by_sku["OK-001"]["is_low_stock"] is False


def test_stock_health_limit(client: TestClient) -> None:
    for i in range(5):
        _make_product(client, f"LIM-{i:03d}", stock=i * 10, reorder=5)

    items = client.get("/reports/inventory/stock-health?limit=3").json()
    assert len(items) <= 3
