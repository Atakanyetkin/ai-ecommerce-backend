import enum


class ProductStatus(str, enum.Enum):
    """Derived status for products based on stock_quantity and is_active flag."""

    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    INACTIVE = "inactive"
