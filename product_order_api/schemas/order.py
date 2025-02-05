"""Order schema module."""
from datetime import datetime
from enum import Enum
from typing import List
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    NonNegativeFloat,
    NonNegativeInt
)


class OrderStatus(str, Enum):
    """Enum for order status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# PUBLIC_INTERFACE
class OrderItemBase(BaseModel):
    """Base schema for OrderItem."""
    product_id: int
    quantity: NonNegativeInt = Field(..., gt=0)


# PUBLIC_INTERFACE
class OrderItemCreate(OrderItemBase):
    """Schema for creating a new order item."""
    pass


# PUBLIC_INTERFACE
class OrderItemResponse(OrderItemBase):
    """Schema for order item response including all fields."""
    id: int
    unit_price: NonNegativeFloat
    subtotal: NonNegativeFloat

    class Config:
        """Pydantic config for ORM mode."""
        from_attributes = True


# PUBLIC_INTERFACE
class OrderBase(BaseModel):
    """Base schema for Order."""
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: EmailStr


# PUBLIC_INTERFACE
class OrderCreate(OrderBase):
    """Schema for creating a new order."""
    items: List[OrderItemCreate]


# PUBLIC_INTERFACE
class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    status: OrderStatus


# PUBLIC_INTERFACE
class OrderResponse(OrderBase):
    """Schema for order response including all fields."""
    id: int
    total_amount: NonNegativeFloat
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItemResponse]

    class Config:
        """Pydantic config for ORM mode."""
        from_attributes = True
