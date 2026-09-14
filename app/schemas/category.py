import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Base Category fields."""

    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    parent_id: uuid.UUID | None = None
    image_url: str | None = None
    is_active: bool = True
    display_order: int = 0


class CategoryCreate(CategoryBase):
    """Payload for creating a new category."""

    pass


class CategoryUpdate(BaseModel):
    """Payload for updating an existing category."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    parent_id: uuid.UUID | None = None
    image_url: str | None = None
    is_active: bool | None = None
    display_order: int | None = None


class CategoryResponse(CategoryBase):
    """Public representation of a Category."""

    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryTreeResponse(CategoryResponse):
    """Hierarchical category tree node with nested children."""

    children: list["CategoryTreeResponse"] = []

    model_config = ConfigDict(from_attributes=True)
