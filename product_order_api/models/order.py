"""Order and OrderItem models module."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


# PUBLIC_INTERFACE
class Order(Base):
    """
    Order model representing customer orders.

    Attributes:
        id (int): Primary key
        customer_name (str): Name of the customer
        customer_email (str): Email of the customer
        total_amount (float): Total order amount
        status (str): Order status
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
        order_items (list): List of order items
    """
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, index=True)
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
        back_populates="order",
        cascade="all, delete-orphan"
    )


# PUBLIC_INTERFACE
class OrderItem(Base):
    """
    OrderItem model representing items within an order.

    Attributes:
        id (int): Primary key
        order_id (int): Foreign key to Order
        product_id (int): Foreign key to Product
        quantity (int): Quantity ordered
        unit_price (float): Price per unit
        subtotal (float): Total price for this item
        order (Order): Order relationship
        product (Product): Product relationship
    """
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey('orders.id'),
        nullable=False,
        index=True
    )
    product_id = Column(
        Integer,
        ForeignKey('products.id'),
        nullable=False,
        index=True
    )
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
