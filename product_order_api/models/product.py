"""Product model module."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from src.database import Base


# PUBLIC_INTERFACE
class Product(Base):
    """
    Product model representing items available for purchase.

    Attributes:
        id (int): Primary key
        name (str): Product name
        description (str): Product description
        price (float): Product price
        stock (int): Available stock quantity
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000))
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationship with OrderItem
    order_items = relationship(
        "OrderItem",
        back_populates="product",
        cascade="all, delete-orphan"
    )
