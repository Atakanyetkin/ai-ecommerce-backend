import pytest
from fastapi.testclient import TestClient

from app import crud
from app.core.security import create_access_token
from app.models.product import UnitType
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate


@pytest.fixture
def superuser_headers(db_session):
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        email="admin2@example.com",
        username="adminuser2",
        hashed_password=hash_password("AdminPass123!"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_product_derived_status_out_of_stock(client: TestClient, db_session):
    """Verify stock_quantity=0 dynamically returns status='out_of_stock'."""
    cat = crud.create_category(
        db_session, CategoryCreate(name="Stok Test", description="Test")
    )
    prod = crud.create_product(
        db_session,
        ProductCreate(
            name="Tükenmiş Ürün",
            category_id=cat.id,
            price=50.0,
            unit=UnitType.KG,
            unit_amount=1.0,
            stock_quantity=0.0,  # Zero stock
            sku="OUT-STK-01",
        ),
    )

    response = client.get(f"/api/v1/products/{prod.slug}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "out_of_stock"


def test_product_derived_status_inactive(client: TestClient, db_session):
    """Verify is_active=False dynamically returns status='inactive'."""
    cat = crud.create_category(
        db_session, CategoryCreate(name="Pasif Test", description="Test")
    )
    prod = crud.create_product(
        db_session,
        ProductCreate(
            name="Pasif Ürün",
            category_id=cat.id,
            price=50.0,
            unit=UnitType.KG,
            unit_amount=1.0,
            stock_quantity=100.0,
            sku="INACTV-01",
            is_active=False,  # Inactive
        ),
    )

    # Fetch with status=inactive filter
    response = client.get("/api/v1/products?status=inactive")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "inactive"


def test_invalid_price_and_negative_stock_validation(client: TestClient, db_session, superuser_headers):
    """Verify negative stock and zero/negative price fail validation."""
    cat = crud.create_category(
        db_session, CategoryCreate(name="Validasyon Test", description="Test")
    )

    # 1. Invalid price <= 0
    payload_invalid_price = {
        "name": "Geçersiz Fiyatlı Ürün",
        "category_id": str(cat.id),
        "price": 0.0,  # invalid price
        "unit": "kg",
        "unit_amount": 1.0,
        "stock_quantity": 10.0,
        "sku": "INV-PRC-01",
    }
    resp1 = client.post("/api/v1/products", json=payload_invalid_price, headers=superuser_headers)
    assert resp1.status_code in [400, 422]

    # 2. Negative stock < 0
    payload_negative_stock = {
        "name": "Negatif Stoklu Ürün",
        "category_id": str(cat.id),
        "price": 10.0,
        "unit": "kg",
        "unit_amount": 1.0,
        "stock_quantity": -5.0,  # negative stock
        "sku": "NEG-STK-01",
    }
    resp2 = client.post("/api/v1/products", json=payload_negative_stock, headers=superuser_headers)
    assert resp2.status_code in [400, 422]


def test_filter_by_status(client: TestClient, db_session):
    """Verify filtering products by derived status parameter."""
    cat = crud.create_category(
        db_session, CategoryCreate(name="Filter Status Test", description="Test")
    )
    crud.create_product(
        db_session,
        ProductCreate(
            name="Stokta Var",
            category_id=cat.id,
            price=20.0,
            unit=UnitType.KG,
            unit_amount=1.0,
            stock_quantity=50.0,
            sku="STK-VAR-01",
        ),
    )
    crud.create_product(
        db_session,
        ProductCreate(
            name="Stokta Yok",
            category_id=cat.id,
            price=20.0,
            unit=UnitType.KG,
            unit_amount=1.0,
            stock_quantity=0.0,
            sku="STK-YOK-01",
        ),
    )

    resp_in_stock = client.get("/api/v1/products?status=in_stock")
    assert resp_in_stock.status_code == 200
    assert any(p["sku"] == "STK-VAR-01" for p in resp_in_stock.json()["items"])

    resp_out_stock = client.get("/api/v1/products?status=out_of_stock")
    assert resp_out_stock.status_code == 200
    assert any(p["sku"] == "STK-YOK-01" for p in resp_out_stock.json()["items"])
