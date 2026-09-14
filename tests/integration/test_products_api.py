import pytest
from fastapi.testclient import TestClient


def test_list_products_pagination_structure(client: TestClient):
    """Verify GET /api/v1/products returns paginated envelope."""
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "pages" in data
    assert isinstance(data["items"], list)


def test_create_product_admin_required(client: TestClient):
    """Verify normal/unauthenticated users cannot create products (401/403)."""
    payload = {
        "name": "Test Domates",
        "category_id": "00000000-0000-0000-0000-000000000000",
        "price": 25.0,
        "unit": "kg",
        "unit_amount": 1.0,
        "stock_quantity": 50.0,
        "sku": "TEST-DOM-01",
    }
    response = client.post("/api/v1/products", json=payload)
    assert response.status_code in [401, 403]
