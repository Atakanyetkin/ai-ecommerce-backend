import math
import uuid
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app import crud
from app.core.enums import ProductStatus
from app.models.product import Product, UnitType
from app.schemas.product import ProductCreate, ProductUpdate


def get_product_by_id_or_slug(db: Session, id_or_slug: str) -> Product:
    """Fetch product by UUID string or slug. Raises 404 if not found."""
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


def list_products(
    db: Session,
    category_id: uuid.UUID | None = None,
    category_slug: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    unit: UnitType | None = None,
    status_filter: ProductStatus | None = None,
    search: str | None = None,
    is_organic: bool | None = None,
    sort_by: str = "newest",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Product], int, int]:
    """List, filter, and paginate products.

    Applies status_filter logic (in_stock, out_of_stock, inactive).
    """
    query = db.query(Product).options(joinedload(Product.category))

    # Apply status filter
    if status_filter:
        if status_filter == ProductStatus.INACTIVE:
            query = query.filter(Product.is_active.is_(False))
        elif status_filter == ProductStatus.OUT_OF_STOCK:
            query = query.filter(Product.is_active.is_(True), Product.stock_quantity <= 0)
        elif status_filter == ProductStatus.IN_STOCK:
            query = query.filter(Product.is_active.is_(True), Product.stock_quantity > 0)
    else:
        # Default behavior: show active products unless explicitly requested inactive
        query = query.filter(Product.is_active.is_(True))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if category_slug:
        cat = crud.get_category_by_slug(db, category_slug)
        if cat:
            child_ids = [c.id for c in cat.children] if cat.children else []
            query = query.filter(Product.category_id.in_([cat.id] + child_ids))
        else:
            return [], 0, 0

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if unit is not None:
        query = query.filter(Product.unit == unit)

    if is_organic is not None:
        query = query.filter(Product.is_organic == is_organic)

    if search:
        search_kw = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_kw),
                Product.description.ilike(search_kw),
                Product.origin.ilike(search_kw),
                Product.sku.ilike(search_kw),
            )
        )

    total = query.count()

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "name_asc":
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()
    pages = math.ceil(total / limit) if limit > 0 else 1

    return items, total, pages


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """Create a new product with category validation and SKU conflict handling."""
    if not crud.get_category_by_id(db, product_in.category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified category_id does not exist",
        )

    if crud.get_product_by_sku(db, product_in.sku):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists",
        )

    return crud.create_product(db, product_in)


def update_product(db: Session, product_id: uuid.UUID, product_in: ProductUpdate) -> Product:
    """Update product by ID."""
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


def delete_product(db: Session, product_id: uuid.UUID) -> None:
    """Delete product by ID."""
    product = crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    crud.delete_product(db, product)
