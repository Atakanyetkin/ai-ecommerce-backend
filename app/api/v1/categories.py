import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.deps import get_current_superuser
from app.db.database import get_db
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeResponse,
    CategoryUpdate,
)

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
    if crud.get_category_by_slug(db, crud.slugify(category_in.name)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists",
        )
    return crud.create_category(db, category_in)


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
    category = crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return crud.update_category(db, category, category_in)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category (Superuser only)",
)
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    category = crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    crud.delete_category(db, category)
    return None
