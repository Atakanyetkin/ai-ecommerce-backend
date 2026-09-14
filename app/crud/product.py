import math
import uuid
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.crud.category import get_category_by_slug, slugify
from app.models.category import Category
from app.models.product import Product, UnitType
from app.schemas.product import ProductCreate, ProductUpdate


def get_product_by_id(db: Session, product_id: uuid.UUID) -> Product | None:
    """Fetch product by ID with eager category loading."""
    return (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.id == product_id)
        .first()
    )


def get_product_by_slug(db: Session, slug: str) -> Product | None:
    """Fetch product by slug with eager category loading."""
    return (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.slug == slug)
        .first()
    )


def get_product_by_sku(db: Session, sku: str) -> Product | None:
    """Fetch product by SKU."""
    return db.query(Product).filter(Product.sku == sku.strip().upper()).first()


def get_products(
    db: Session,
    category_id: uuid.UUID | None = None,
    category_slug: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    unit: UnitType | None = None,
    search: str | None = None,
    is_organic: bool | None = None,
    active_only: bool = True,
    sort_by: str = "newest",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Product], int, int]:
    """Fetch paginated, filtered, and sorted products for Grocery catalog.

    Returns tuple (items, total_count, total_pages).
    """
    query = db.query(Product).options(joinedload(Product.category))

    if active_only:
        query = query.filter(Product.is_active.is_(True))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if category_slug:
        cat = get_category_by_slug(db, category_slug)
        if cat:
            # Include child categories if hierarchical
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

    # Total count before pagination
    total = query.count()

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "name_asc":
        query = query.order_by(Product.name.asc())
    else:  # newest (default)
        query = query.order_by(Product.created_at.desc())

    # Pagination
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()
    pages = math.ceil(total / limit) if limit > 0 else 1

    return items, total, pages


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """Create a new product with auto-generated slug."""
    base_slug = slugify(product_in.name)
    slug = base_slug
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    db_product = Product(
        name=product_in.name.strip(),
        slug=slug,
        description=product_in.description,
        category_id=product_in.category_id,
        price=product_in.price,
        discount_price=product_in.discount_price,
        unit=product_in.unit,
        unit_amount=product_in.unit_amount,
        stock_quantity=product_in.stock_quantity,
        sku=product_in.sku.strip().upper(),
        image_url=product_in.image_url,
        is_organic=product_in.is_organic,
        origin=product_in.origin,
        is_active=product_in.is_active,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product: Product, product_in: ProductUpdate) -> Product:
    """Update an existing product."""
    update_data = product_in.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"]:
        new_name = update_data["name"].strip()
        product.name = new_name
        base_slug = slugify(new_name)
        slug = base_slug
        counter = 1
        while db.query(Product).filter(Product.slug == slug, Product.id != product.id).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        product.slug = slug

    if "sku" in update_data and update_data["sku"]:
        update_data["sku"] = update_data["sku"].strip().upper()

    for field, value in update_data.items():
        if field != "name":
            setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    """Delete a product."""
    db.delete(product)
    db.commit()
