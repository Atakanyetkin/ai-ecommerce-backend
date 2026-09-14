import pytest
from fastapi.testclient import TestClient

from app import crud
from app.core.security import create_access_token
from app.models.product import UnitType
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate


@pytest.fixture
def superuser_headers(db_session):
    """Create a superuser and return Authorization headers."""
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=hash_password("AdminPass123!"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_list_categories(client: TestClient):
    """Verify public GET /api/v1/categories returns category list."""
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_category_admin(client: TestClient, superuser_headers):
    """Verify admin superuser can create a category."""
    payload = {
        "name": "Fırın & Pastane",
        "description": "Taze ekmek ve hamur işleri",
    }
    response = client.post("/api/v1/categories", json=payload, headers=superuser_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Fırın & Pastane"
    assert data["slug"] == "firin-pastane"
    assert data["is_active"] is True


def test_deactivate_category(client: TestClient, db_session, superuser_headers):
    """Verify PATCH /api/v1/categories/{id}/deactivate sets is_active to False."""
    cat = crud.create_category(
        db_session, CategoryCreate(name="Atıştırmalık", description="Bisküvi ve çikolata")
    )

    response = client.patch(
        f"/api/v1/categories/{cat.id}/deactivate", headers=superuser_headers
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_safe_category_deletion_with_attached_products(
    client: TestClient, db_session, superuser_headers
):
    """Verify deleting a category with attached products deactivates (soft deletes) instead of hard deleting."""
    cat = crud.create_category(
        db_session, CategoryCreate(name="Organik Sebzeler", description="Organik sebze")
    )
    prod = crud.create_product(
        db_session,
        ProductCreate(
            name="Organik Biber",
            category_id=cat.id,
            price=35.0,
            unit=UnitType.KG,
            unit_amount=1.0,
            stock_quantity=20.0,
            sku="ORG-BIB-01",
        ),
    )

    # Attempt delete category
    response = client.delete(f"/api/v1/categories/{cat.id}", headers=superuser_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "deactivated"

    # Category should still exist in DB but be inactive
    updated_cat = crud.get_category_by_id(db_session, cat.id)
    assert updated_cat is not None
    assert updated_cat.is_active is False


def test_get_category_products(client: TestClient, db_session):
    """Verify GET /api/v1/categories/{id_or_slug}/products lists category products."""
    cat = crud.create_category(
        db_session, CategoryCreate(name="Deneme Kategori", description="Açıklama")
    )
    crud.create_product(
        db_session,
        ProductCreate(
            name="Deneme Ürün",
            category_id=cat.id,
            price=15.0,
            unit=UnitType.PIECE,
            unit_amount=1.0,
            stock_quantity=10.0,
            sku="DEN-PROD-01",
        ),
    )

    response = client.get(f"/api/v1/categories/{cat.slug}/products")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Deneme Ürün"
