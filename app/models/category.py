import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Category(Base):
    """Category model for Grocery catalog supporting hierarchical parent-child trees."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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
    parent: Mapped["Category | None"] = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="Category.display_order",
    )
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name='{self.name}' slug='{self.slug}'>"
