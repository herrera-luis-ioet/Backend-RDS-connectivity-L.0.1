"""Product schema module."""
from datetime import datetime
from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt


# PUBLIC_INTERFACE
class ProductBase(BaseModel):
    """Base schema for Product with common attributes."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    price: NonNegativeFloat
    stock: NonNegativeInt


# PUBLIC_INTERFACE
class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


# PUBLIC_INTERFACE
class ProductUpdate(BaseModel):
    """Schema for updating a product with optional fields."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    price: NonNegativeFloat | None = None
    stock: NonNegativeInt | None = None


# PUBLIC_INTERFACE
class ProductResponse(ProductBase):
    """Schema for product response including all fields."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM mode."""
        from_attributes = True
