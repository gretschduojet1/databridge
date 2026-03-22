from fastapi.testclient import TestClient


def test_list_jobs_empty(client: TestClient) -> None:
    response = client.get("/jobs/")
    assert response.status_code == 200
    assert response.json() == []


def test_dispatch_report(client: TestClient) -> None:
    response = client.post("/jobs/dispatch/report")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"


def test_get_job_after_dispatch(client: TestClient) -> None:
    dispatch = client.post("/jobs/dispatch/report").json()
    job_id = dispatch["job_id"]

    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["id"] == job_id


def test_get_job_not_found(client: TestClient) -> None:
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_dispatch_export_customers(client: TestClient) -> None:
    response = client.post("/jobs/dispatch/export?resource=customers")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_dispatch_export_unknown_resource(client: TestClient) -> None:
    response = client.post("/jobs/dispatch/export?resource=invoices")
    assert response.status_code == 400


def test_list_jobs_after_dispatch(client: TestClient) -> None:
    client.post("/jobs/dispatch/report")
    response = client.get("/jobs/")
    assert response.status_code == 200
    assert len(response.json()) >= 1
