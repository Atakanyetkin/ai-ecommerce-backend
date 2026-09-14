import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class UnitType(str, enum.Enum):
    """Measurement unit type for grocery products."""

    KG = "kg"
    GRAM = "gram"
    PIECE = "piece"
    LITER = "liter"
    PACK = "pack"


class Product(Base):
    """Product model for Online Grocery catalog with unit pricing and stock."""

    __tablename__ = "products"

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
    unit_amount: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # e.g. 1.0 kg, 500.0 gram, 1.5 liter
    stock_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_organic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    origin: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "Antalya", "Balıkesir"

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

    def __repr__(self) -> str:
        return f"<Product id={self.id} name='{self.name}' unit={self.unit} price={self.price}>"
