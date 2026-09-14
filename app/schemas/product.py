import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.models.product import UnitType
from app.schemas.category import CategoryResponse


class ProductBase(BaseModel):
    """Base Product fields for Grocery catalog."""

    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    category_id: uuid.UUID
    price: Decimal = Field(gt=0, decimal_places=2)
    discount_price: Decimal | None = Field(default=None, decimal_places=2)
    unit: UnitType = UnitType.KG
    unit_amount: float = Field(default=1.0, gt=0)
    stock_quantity: float = Field(default=0.0, ge=0)
    sku: str = Field(min_length=3, max_length=100)
    image_url: str | None = None
    is_organic: bool = False
    origin: str | None = None
    is_active: bool = True


class ProductCreate(ProductBase):
    """Payload for creating a new product."""

    pass


class ProductUpdate(BaseModel):
    """Payload for updating an existing product."""

    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    category_id: uuid.UUID | None = None
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    discount_price: Decimal | None = Field(default=None, decimal_places=2)
    unit: UnitType | None = None
    unit_amount: float | None = Field(default=None, gt=0)
    stock_quantity: float | None = Field(default=None, ge=0)
    sku: str | None = Field(default=None, min_length=3, max_length=100)
    image_url: str | None = None
    is_organic: bool | None = None
    origin: str | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    """Public representation of a Product."""

    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Paginated product list envelope."""

    items: list[ProductResponse]
    total: int
    page: int
    limit: int
    pages: int
