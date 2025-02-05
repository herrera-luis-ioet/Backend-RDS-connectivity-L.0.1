"""Orders router module."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.database import get_db
from src.errors import (
    ResourceNotFoundError,
    DatabaseError,
    BusinessLogicError
)
from src.models.order import Order, OrderItem
from src.models.product import Product
from src.schemas.order import (
    OrderCreate, OrderResponse, OrderUpdate, OrderStatus
)

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


# PUBLIC_INTERFACE
@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="""
    Create a new order with multiple items.
    
    The endpoint will:
    - Validate product existence and stock availability
    - Calculate total amount
    - Update product stock levels
    - Create order with items
    """,
    responses={
        201: {
            "description": "Order created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "customer_name": "John Doe",
                        "customer_email": "john@example.com",
                        "total_amount": 159.97,
                        "status": "PENDING",
                        "order_items": [
                            {
                                "id": 1,
                                "product_id": 1,
                                "quantity": 2,
                                "unit_price": 29.99,
                                "subtotal": 59.98
                            },
                            {
                                "id": 2,
                                "product_id": 2,
                                "quantity": 1,
                                "unit_price": 99.99,
                                "subtotal": 99.99
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Product not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Product with id 1 not found"
                    }
                }
            }
        },
        400: {
            "description": "Business logic error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient stock for product 1. Available: 5, Requested: 10"
                    }
                }
            }
        },
        500: {
            "description": "Database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error creating order: Database error"
                    }
                }
            }
        }
    }
)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    Create a new order with items.

    Args:
        order (OrderCreate): Order data including items
        db (Session): Database session

    Returns:
        OrderResponse: Created order with all details

    Raises:
        HTTPException: If products don't exist or insufficient stock
    """
    try:
        # Create new order instance
        db_order = Order(
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            total_amount=0,  # Will be calculated from items
            status=OrderStatus.PENDING
        )

        total_amount = 0
        order_items = []

        # Process each order item
        for item in order.items:
            # Get product and validate
            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )
            if not product:
                raise ResourceNotFoundError("Product", item.product_id)
            # Check stock availability
            if product.stock < item.quantity:
                msg = (
                    f"Insufficient stock for product {product.id}. "
                    f"Available: {product.stock}, Requested: {item.quantity}"
                )
                raise BusinessLogicError(msg)

            # Create order item
            subtotal = product.price * item.quantity
            order_item = OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price,
                subtotal=subtotal
            )
            # Update product stock
            product.stock -= item.quantity
            total_amount += subtotal
            order_items.append(order_item)
        # Update order total and items
        db_order.total_amount = total_amount
        db_order.order_items = order_items

        # Save to database
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Error creating order: {str(e)}")


# PUBLIC_INTERFACE
@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List all orders",
    description="Get a paginated list of all orders with their items",
    responses={
        200: {
            "description": "List of orders retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "customer_name": "John Doe",
                            "customer_email": "john@example.com",
                            "total_amount": 159.97,
                            "status": "COMPLETED",
                            "order_items": [
                                {
                                    "id": 1,
                                    "product_id": 1,
                                    "quantity": 2,
                                    "unit_price": 29.99,
                                    "subtotal": 59.98
                                }
                            ]
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error listing orders: Database error"
                    }
                }
            }
        }
    }
)
def list_orders(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List all orders with pagination.

    Args:
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        db (Session): Database session

    Returns:
        List[OrderResponse]: List of orders
    """
    try:
        orders = db.query(Order).offset(skip).limit(limit).all()
        return orders
    except SQLAlchemyError as e:
        raise DatabaseError(f"Error listing orders: {str(e)}")


# PUBLIC_INTERFACE
@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get a specific order",
    description="Get detailed information about a specific order by its ID",
    responses={
        200: {
            "description": "Order found and returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "customer_name": "John Doe",
                        "customer_email": "john@example.com",
                        "total_amount": 159.97,
                        "status": "PROCESSING",
                        "order_items": [
                            {
                                "id": 1,
                                "product_id": 1,
                                "quantity": 2,
                                "unit_price": 29.99,
                                "subtotal": 59.98
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Order not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Order with id 1 not found"
                    }
                }
            }
        },
        500: {
            "description": "Database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error retrieving order: Database error"
                    }
                }
            }
        }
    }
)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """
    Get a specific order by ID.

    Args:
        order_id (int): Order ID
        db (Session): Database session

    Returns:
        OrderResponse: Order details

    Raises:
        HTTPException: If order not found
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundError("Order", order_id)
        return order
    except SQLAlchemyError as e:
        raise DatabaseError(f"Error retrieving order: {str(e)}")


# PUBLIC_INTERFACE
@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db)
):
    """
    Update order status.

    Args:
        order_id (int): Order ID
        order_update (OrderUpdate): Update data
        db (Session): Database session

    Returns:
        OrderResponse: Updated order

    Raises:
        HTTPException: If order not found or invalid status transition
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundError("Order", order_id)

        # Validate status transition
        current_status = OrderStatus(order.status)
        new_status = order_update.status

        # Define valid status transitions
        valid_transitions = {
            OrderStatus.PENDING: {
                OrderStatus.PROCESSING,
                OrderStatus.CANCELLED
            },
            OrderStatus.PROCESSING: {
                OrderStatus.COMPLETED,
                OrderStatus.CANCELLED
            },
            OrderStatus.COMPLETED: set(),  # No transitions from completed
            OrderStatus.CANCELLED: set()  # No transitions from cancelled
        }

        if new_status not in valid_transitions[current_status]:
            valid_trans = ', '.join(
                str(s) for s in valid_transitions[current_status]
            )
            msg = (
                f"Invalid status transition from {current_status} "
                f"to {new_status}. Valid transitions are: {valid_trans}"
            )
            raise BusinessLogicError(msg)

        # If cancelling order, restore product stock
        if (new_status == OrderStatus.CANCELLED and
                current_status != OrderStatus.CANCELLED):
            for item in order.order_items:
                product = (
                    db.query(Product)
                    .filter(Product.id == item.product_id)
                    .first()
                )
                if product:
                    product.stock += item.quantity

        order.status = new_status
        db.commit()
        db.refresh(order)
        return order

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Error updating order: {str(e)}")


# PUBLIC_INTERFACE
@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """
    Delete an order.

    Args:
        order_id (int): Order ID
        db (Session): Database session

    Raises:
        HTTPException: If order not found or cannot be deleted
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundError("Order", order_id)

        # Restore product stock if order is not cancelled
        if order.status != OrderStatus.CANCELLED:
            for item in order.order_items:
                product = (
                    db.query(Product)
                    .filter(Product.id == item.product_id)
                    .first()
                )
                if product:
                    product.stock += item.quantity

        db.delete(order)
        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Error deleting order: {str(e)}")
