from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.product import Product
from models.store import StoreLocation, StoreStock
from schemas.enums import Category


def _create_product(db: Session, sku: str = "SKU-001", category: Category = Category.ELECTRONICS) -> Product:
    product = Product(
        sku=sku,
        name=f"Product {sku}",
        category=category,
        stock_qty=100,
        reorder_level=10,
        updated_at=datetime.now(UTC),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _create_store(
    db: Session, name: str = "Test Store", city: str = "Boston", region: str = "Northeast"
) -> StoreLocation:
    store = StoreLocation(name=name, city=city, region=region, created_at=datetime.now(UTC))
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def _add_stock(db: Session, store_id: int, product_id: int, qty: int, reorder: int) -> StoreStock:
    stock = StoreStock(
        store_id=store_id,
        product_id=product_id,
        qty_on_hand=qty,
        reorder_level=reorder,
        updated_at=datetime.now(UTC),
    )
    db.add(stock)
    db.commit()
    return stock


def test_list_stores_empty(client: TestClient) -> None:
    response = client.get("/stores/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_list_stores(client: TestClient, db: Session) -> None:
    _create_store(db, "Boston Flagship", "Boston", "Northeast")
    _create_store(db, "Chicago Loop", "Chicago", "Midwest")

    response = client.get("/stores/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    names = {s["name"] for s in data["items"]}
    assert names == {"Boston Flagship", "Chicago Loop"}


def test_filter_by_region(client: TestClient, db: Session) -> None:
    _create_store(db, "Atlanta Central", "Atlanta", "Southeast")
    _create_store(db, "Miami Beach", "Miami", "Southeast")
    _create_store(db, "Seattle Center", "Seattle", "West")

    response = client.get("/stores/?region=Southeast")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(s["region"] == "Southeast" for s in data["items"])


def test_search_by_name(client: TestClient, db: Session) -> None:
    _create_store(db, "San Francisco Bay", "San Francisco", "West")
    _create_store(db, "Los Angeles Main", "Los Angeles", "West")

    response = client.get("/stores/?search=francisco")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "San Francisco Bay"


def test_low_stock_count(client: TestClient, db: Session) -> None:
    product = _create_product(db, "SKU-LOW-001")
    store = _create_store(db, "Low Stock Store", "Detroit", "Midwest")
    # qty 5 < reorder 20 → low stock
    _add_stock(db, store.id, product.id, qty=5, reorder=20)

    response = client.get("/stores/")
    assert response.status_code == 200
    result = next(s for s in response.json()["items"] if s["id"] == store.id)
    assert result["low_stock_count"] == 1
    assert result["total_products"] == 1


def test_all_stocked(client: TestClient, db: Session) -> None:
    product = _create_product(db, "SKU-OK-001")
    store = _create_store(db, "Well Stocked Store", "New York", "Northeast")
    # qty 50 > reorder 10 → not low stock
    _add_stock(db, store.id, product.id, qty=50, reorder=10)

    response = client.get("/stores/")
    result = next(s for s in response.json()["items"] if s["id"] == store.id)
    assert result["low_stock_count"] == 0


def test_get_store_by_id(client: TestClient, db: Session) -> None:
    product = _create_product(db, "SKU-DETAIL-001")
    store = _create_store(db, "Detail Store", "Philadelphia", "Northeast")
    _add_stock(db, store.id, product.id, qty=3, reorder=15)

    response = client.get(f"/stores/{store.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Detail Store"
    assert len(data["inventory"]) == 1
    item = data["inventory"][0]
    assert item["sku"] == "SKU-DETAIL-001"
    assert item["qty_on_hand"] == 3
    assert item["reorder_level"] == 15
    assert item["is_low_stock"] is True


def test_get_store_not_found(client: TestClient) -> None:
    response = client.get("/stores/99999")
    assert response.status_code == 404


def test_low_stock_only_filter(client: TestClient, db: Session) -> None:
    product = _create_product(db, "SKU-FILTER-001")
    low_store = _create_store(db, "Low Store", "Denver", "West")
    ok_store = _create_store(db, "OK Store", "Portland", "West")
    _add_stock(db, low_store.id, product.id, qty=2, reorder=10)
    _add_stock(db, ok_store.id, product.id, qty=50, reorder=10)

    response = client.get("/stores/?low_stock_only=true")
    assert response.status_code == 200
    names = {s["name"] for s in response.json()["items"]}
    assert "Low Store" in names
    assert "OK Store" not in names
