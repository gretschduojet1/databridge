from fastapi.testclient import TestClient

from schemas.enums import Region


def test_list_customers_empty(client: TestClient) -> None:
    response = client.get("/customers/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_create_customer(client: TestClient) -> None:
    payload = {"name": "Jane Smith", "email": "jane@example.com", "region": Region.WEST}
    response = client.post("/customers/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Smith"
    assert data["email"] == "jane@example.com"
    assert data["region"] == Region.WEST
    assert "id" in data
    assert "created_at" in data


def test_get_customer_by_id(client: TestClient) -> None:
    payload = {"name": "John Doe", "email": "john@example.com", "region": Region.NORTHEAST}
    created = client.post("/customers/", json=payload).json()

    response = client.get(f"/customers/{created['id']}")
    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"


def test_get_customer_not_found(client: TestClient) -> None:
    response = client.get("/customers/99999")
    assert response.status_code == 404


def test_filter_customers_by_region(client: TestClient) -> None:
    client.post("/customers/", json={"name": "Alice", "email": "alice@example.com", "region": Region.MIDWEST})
    client.post("/customers/", json={"name": "Bob", "email": "bob@example.com", "region": Region.WEST})

    response = client.get("/customers/?region=Midwest")
    assert response.status_code == 200
    results = response.json()["items"]
    assert all(c["region"] == Region.MIDWEST for c in results)
