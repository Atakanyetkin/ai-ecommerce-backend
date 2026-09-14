import pytest
from fastapi.testclient import TestClient


def test_list_categories(client: TestClient):
    """Verify public GET /api/v1/categories returns category list."""
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_category_admin_required(client: TestClient):
    """Verify normal users/unauthenticated requests cannot create categories (401/403)."""
    payload = {
        "name": "Test Kategori",
        "description": "Test açıklama",
    }
    response = client.post("/api/v1/categories", json=payload)
    assert response.status_code in [401, 403]
