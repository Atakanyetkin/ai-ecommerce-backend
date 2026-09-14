import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.deps import get_current_superuser
from app.db.database import get_db
from app.models.product import UnitType
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=ProductListResponse,
    summary="List and search Grocery products",
    description="Filter grocery catalog by category, price range, unit type, search query, or organic flag with pagination.",
)
def list_products(
    category_id: uuid.UUID | None = Query(default=None, description="Filter by Category UUID"),
    category_slug: str | None = Query(default=None, description="Filter by Category slug (e.g. meyve-sebze)"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price filter"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price filter"),
    unit: UnitType | None = Query(default=None, description="Filter by unit (kg, gram, piece, liter, pack)"),
    search: str | None = Query(default=None, description="Search keyword in product name, description, origin, or SKU"),
    is_organic: bool | None = Query(default=None, description="Filter organic products"),
    sort_by: Literal["newest", "price_asc", "price_desc", "name_asc"] = Query(default="newest", description="Sorting criteria"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    items, total, pages = crud.get_products(
        db,
        category_id=category_id,
        category_slug=category_slug,
        min_price=min_price,
        max_price=max_price,
        unit=unit,
        search=search,
        is_organic=is_organic,
        sort_by=sort_by,
        page=page,
        limit=limit,
    )
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get(
    "/{id_or_slug}",
    response_model=ProductResponse,
    summary="Get product by ID or slug",
)
def get_product(id_or_slug: str, db: Session = Depends(get_db)) -> ProductResponse:
    product = None
    try:
        prod_uuid = uuid.UUID(id_or_slug)
        product = crud.get_product_by_id(db, prod_uuid)
    except ValueError:
        product = crud.get_product_by_slug(db, id_or_slug)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product (Superuser only)",
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> ProductResponse:
    # Verify category exists
    if not crud.get_category_by_id(db, product_in.category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified category_id does not exist",
        )

    # Check SKU uniqueness
    if crud.get_product_by_sku(db, product_in.sku):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this SKU already exists",
        )

    return crud.create_product(db, product_in)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product (Superuser only)",
)
def update_product(
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> ProductResponse:
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if product_in.category_id and not crud.get_category_by_id(db, product_in.category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified category_id does not exist",
        )

    return crud.update_product(db, product, product_in)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product (Superuser only)",
)
def delete_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    crud.delete_product(db, product)
    return None
