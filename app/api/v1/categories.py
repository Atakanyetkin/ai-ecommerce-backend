import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.deps import get_current_superuser
from app.db.database import get_db
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.schemas.product import ProductListResponse
from app.services import category_service

router = APIRouter()


@router.get(
    "",
    summary="List all categories",
    description="Fetch flat category list or hierarchical tree by setting tree=true.",
)
def list_categories(
    tree: bool = Query(default=False, description="Return hierarchical parent-child category tree"),
    active_only: bool = Query(default=True, description="Only return active categories"),
    db: Session = Depends(get_db),
) -> Any:
    if tree:
        return crud.get_category_tree(db, active_only=active_only)
    return crud.get_categories(db, active_only=active_only)


@router.get(
    "/{id_or_slug}",
    response_model=CategoryResponse,
    summary="Get category by ID or slug",
)
def get_category(id_or_slug: str, db: Session = Depends(get_db)) -> CategoryResponse:
    return category_service.get_category_by_id_or_slug(db, id_or_slug)


@router.get(
    "/{id_or_slug}/products",
    response_model=ProductListResponse,
    summary="List products in category",
)
def get_category_products(
    id_or_slug: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    items, total, pages = category_service.get_category_products(
        db, id_or_slug, page=page, limit=limit
    )
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category (Superuser only)",
)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> CategoryResponse:
    return category_service.create_category(db, category_in)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category (Superuser only)",
)
def update_category(
    category_id: uuid.UUID,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> CategoryResponse:
    return category_service.update_category(db, category_id, category_in)


@router.patch(
    "/{category_id}/deactivate",
    response_model=CategoryResponse,
    summary="Deactivate category (Superuser only)",
)
def deactivate_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> CategoryResponse:
    return category_service.deactivate_category(db, category_id)


@router.delete(
    "/{category_id}",
    summary="Safely delete or deactivate category (Superuser only)",
)
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> Any:
    return category_service.safe_delete_category(db, category_id)
