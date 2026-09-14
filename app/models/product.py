import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ProductStatus
from app.db.database import Base


class UnitType(str, enum.Enum):
    """Measurement unit type for grocery products."""

    KG = "kg"
    GRAM = "gram"
    PIECE = "piece"
    LITER = "liter"
    PACK = "pack"


class Product(Base):
    """Product model for Online Grocery catalog with unit pricing, stock, and check constraints."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("stock_quantity >= 0", name="check_product_stock_quantity_non_negative"),
        CheckConstraint("price > 0", name="check_product_price_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    unit: Mapped[UnitType] = mapped_column(
        Enum(UnitType, name="unit_type_enum"),
        default=UnitType.KG,
        nullable=False,
    )
    unit_amount: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    stock_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_organic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    origin: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")

    @property
    def status(self) -> ProductStatus:
        """Dynamically derive status based on is_active and stock_quantity."""
        if not self.is_active:
            return ProductStatus.INACTIVE
        if self.stock_quantity <= 0:
            return ProductStatus.OUT_OF_STOCK
        return ProductStatus.IN_STOCK

    def __repr__(self) -> str:
        return f"<Product id={self.id} name='{self.name}' status='{self.status.value}' price={self.price}>"
