import uuid
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_category_by_id_or_slug(db: Session, id_or_slug: str) -> Category:
    """Fetch category by UUID string or slug. Raises 404 if not found."""
    category = None
    try:
        cat_uuid = uuid.UUID(id_or_slug)
        category = crud.get_category_by_id(db, cat_uuid)
    except ValueError:
        category = crud.get_category_by_slug(db, id_or_slug)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


def get_category_products(
    db: Session,
    id_or_slug: str,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Product], int, int]:
    """Fetch products belonging to a specific category by ID or slug."""
    category = get_category_by_id_or_slug(db, id_or_slug)
    return crud.get_products(
        db,
        category_id=category.id,
        page=page,
        limit=limit,
    )


def create_category(db: Session, category_in: CategoryCreate) -> Category:
    """Create a category enforcing unique name/slug constraints."""
    slug = crud.slugify(category_in.name)
    if crud.get_category_by_slug(db, slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name already exists",
        )
    return crud.create_category(db, category_in)


def update_category(db: Session, category_id: uuid.UUID, category_in: CategoryUpdate) -> Category:
    """Update category by ID."""
    category = crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return crud.update_category(db, category, category_in)


def deactivate_category(db: Session, category_id: uuid.UUID) -> Category:
    """Deactivate a category (soft deactivate setting is_active=False)."""
    category = crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return crud.update_category(db, category, CategoryUpdate(is_active=False))


def safe_delete_category(db: Session, category_id: uuid.UUID) -> dict[str, Any]:
    """Safely handle category deletion.

    If products are attached to the category, perform soft deactivation instead of hard deleting
    to preserve relational data integrity. If no products attached, perform hard delete.
    """
    category = crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check for attached products
    attached_products_count = db.query(Product).filter(Product.category_id == category.id).count()

    if attached_products_count > 0:
        # Soft delete / Deactivate category to prevent breaking attached products
        crud.update_category(db, category, CategoryUpdate(is_active=False))
        return {
            "action": "deactivated",
            "message": f"Category has {attached_products_count} attached products. Deactivated (soft delete) instead of hard deleting.",
        }

    crud.delete_category(db, category)
    return {"action": "deleted", "message": "Category deleted successfully."}
