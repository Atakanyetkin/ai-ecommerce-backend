import re
import unicodedata
import uuid
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def slugify(text: str) -> str:
    """Generate a clean URL slug from Turkish/international string."""
    text = text.replace("ı", "i").replace("İ", "i").replace("ğ", "g").replace("Ğ", "g")
    text = text.replace("ü", "u").replace("Ü", "u").replace("ş", "s").replace("Ş", "s")
    text = text.replace("ö", "o").replace("Ö", "o").replace("ç", "c").replace("Ç", "c")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def get_category_by_id(db: Session, category_id: uuid.UUID) -> Category | None:
    """Fetch category by ID."""
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_slug(db: Session, slug: str) -> Category | None:
    """Fetch category by slug."""
    return db.query(Category).filter(Category.slug == slug).first()


def get_categories(db: Session, active_only: bool = True) -> list[Category]:
    """Fetch flat list of categories ordered by display_order."""
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active.is_(True))
    return query.order_by(Category.display_order.asc(), Category.name.asc()).all()


def get_category_tree(db: Session, active_only: bool = True) -> list[Category]:
    """Fetch hierarchical root categories with eagerly loaded children."""
    query = db.query(Category).filter(Category.parent_id.is_(None))
    if active_only:
        query = query.filter(Category.is_active.is_(True))
    return (
        query.options(joinedload(Category.children))
        .order_by(Category.display_order.asc(), Category.name.asc())
        .all()
    )


def create_category(db: Session, category_in: CategoryCreate) -> Category:
    """Create a new category with auto-generated slug."""
    base_slug = slugify(category_in.name)
    slug = base_slug
    counter = 1
    while db.query(Category).filter(Category.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    db_category = Category(
        name=category_in.name.strip(),
        slug=slug,
        description=category_in.description,
        parent_id=category_in.parent_id,
        image_url=category_in.image_url,
        is_active=category_in.is_active,
        display_order=category_in.display_order,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category: Category, category_in: CategoryUpdate) -> Category:
    """Update an existing category."""
    update_data = category_in.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"]:
        new_name = update_data["name"].strip()
        category.name = new_name
        base_slug = slugify(new_name)
        slug = base_slug
        counter = 1
        while db.query(Category).filter(Category.slug == slug, Category.id != category.id).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        category.slug = slug

    for field, value in update_data.items():
        if field != "name":
            setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    """Delete a category."""
    db.delete(category)
    db.commit()
