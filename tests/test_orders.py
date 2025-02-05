"""Test module for order endpoints."""
import pytest
from fastapi import status
from product_order_api.schemas.order import OrderStatus
from tests.factories import ProductFactory, OrderFactory, OrderItemFactory


@pytest.mark.asyncio
async def test_create_order_success(test_client, db_session):
    """Test successful order creation with stock management."""
    # Create test products
    product1 = ProductFactory(price=10.0, stock=5, session=db_session)
    product2 = ProductFactory(price=20.0, stock=3, session=db_session)

    # Prepare order data
    order_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "items": [
            {"product_id": product1.id, "quantity": 2},
            {"product_id": product2.id, "quantity": 1}
        ]
    }

    # Create order
    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify response data
    data = response.json()
    assert data["customer_name"] == order_data["customer_name"]
    assert data["customer_email"] == order_data["customer_email"]
    assert data["status"] == OrderStatus.PENDING
    assert len(data["order_items"]) == 2
    assert data["total_amount"] == (2 * 10.0 + 1 * 20.0)

    # Verify stock updates
    db_session.refresh(product1)
    db_session.refresh(product2)
    assert product1.stock == 3  # 5 - 2
    assert product2.stock == 2  # 3 - 1


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(test_client, db_session):
    """Test order creation with insufficient stock."""
    product = ProductFactory(price=10.0, stock=2, session=db_session)
    
    order_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "items": [
            {"product_id": product.id, "quantity": 3}  # Requesting more than available
        ]
    }

    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error_msg = response.json()
    assert "error" in error_msg
    assert "message" in error_msg["error"]
    assert "Insufficient stock" in error_msg["error"]["message"]
    
    # Verify stock wasn't modified
    db_session.refresh(product)
    assert product.stock == 2


@pytest.mark.asyncio
async def test_order_status_transitions(test_client, db_session):
    """Test order status transitions and validation."""
    # Create an order with items
    product = ProductFactory(session=db_session)
    order = OrderFactory(status=OrderStatus.PENDING, session=db_session)
    OrderItemFactory(order=order, product=product, session=db_session)

    # Test valid transitions
    valid_transitions = [
        (OrderStatus.PENDING, OrderStatus.PROCESSING),
        (OrderStatus.PROCESSING, OrderStatus.COMPLETED)
    ]

    for current, next_status in valid_transitions:
        # Set current status
        order.status = current
        db_session.commit()

        # Try transition
        response = await test_client.put(
            f"/orders/{order.id}",
            json={"status": next_status}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == next_status

    # Test invalid transition
    order.status = OrderStatus.COMPLETED
    db_session.commit()
    
    response = await test_client.put(
        f"/orders/{order.id}",
        json={"status": OrderStatus.PROCESSING}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error_msg = response.json()
    assert "error" in error_msg
    assert "message" in error_msg["error"]
    assert "Invalid status transition" in error_msg["error"]["message"]


@pytest.mark.asyncio
async def test_stock_restoration_on_cancellation(test_client, db_session):
    """Test stock restoration when order is cancelled."""
    # Create products and order
    product1 = ProductFactory(stock=10, session=db_session)
    product2 = ProductFactory(stock=15, session=db_session)
    
    order = OrderFactory(status=OrderStatus.PROCESSING, session=db_session)
    OrderItemFactory(
        order=order,
        product=product1,
        quantity=3,
        session=db_session
    )
    OrderItemFactory(
        order=order,
        product=product2,
        quantity=2,
        session=db_session
    )

    # Update stocks to simulate order creation
    product1.stock -= 3
    product2.stock -= 2
    db_session.commit()

    # Cancel the order
    response = await test_client.put(
        f"/orders/{order.id}",
        json={"status": OrderStatus.CANCELLED}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == OrderStatus.CANCELLED

    # Verify stock restoration
    db_session.refresh(product1)
    db_session.refresh(product2)
    assert product1.stock == 10  # Original stock
    assert product2.stock == 15  # Original stock


@pytest.mark.asyncio
async def test_validation_rules(test_client, db_session):
    """Test order validation rules."""
    # Test invalid email
    order_data = {
        "customer_name": "John Doe",
        "customer_email": "invalid-email",
        "items": []
    }
    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test empty customer name
    order_data = {
        "customer_name": "",
        "customer_email": "john@example.com",
        "items": []
    }
    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test negative quantity
    product = ProductFactory(session=db_session)
    order_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "items": [
            {"product_id": product.id, "quantity": -1}
        ]
    }
    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_error_scenarios(test_client, db_session):
    """Test various error scenarios."""
    # Test non-existent product
    order_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "items": [
            {"product_id": 99999, "quantity": 1}
        ]
    }
    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_msg = response.json()
    assert "error" in error_msg
    assert "message" in error_msg["error"]
    assert "Product" in error_msg["error"]["message"]

    # Test non-existent order
    response = await test_client.get("/orders/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_msg = response.json()
    assert "error" in error_msg
    assert "message" in error_msg["error"]
    assert "Order" in error_msg["error"]["message"]

    # Test deleting non-existent order
    response = await test_client.delete("/orders/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_msg = response.json()
    assert "error" in error_msg
    assert "message" in error_msg["error"]
    assert "Order" in error_msg["error"]["message"]


@pytest.mark.asyncio
async def test_list_orders(test_client, db_session):
    """Test listing orders with pagination."""
    # Create multiple orders with items
    for _ in range(5):
        order = OrderFactory(session=db_session)
        product = ProductFactory(session=db_session)
        OrderItemFactory(
            order=order,
            product=product,
            session=db_session
        )
        db_session.commit()

    # Test default pagination
    response = await test_client.get("/orders/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5  # Default limit is 10

    # Test custom pagination
    response = await test_client.get("/orders/?skip=2&limit=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_delete_order(test_client, db_session):
    """Test order deletion with stock restoration."""
    # Create product and order
    product = ProductFactory(stock=10, session=db_session)
    order = OrderFactory(status=OrderStatus.PENDING, session=db_session)
    OrderItemFactory(
        order=order,
        product=product,
        quantity=3,
        session=db_session
    )

    # Update stock to simulate order creation
    product.stock -= 3
    db_session.commit()

    # Delete the order
    response = await test_client.delete(f"/orders/{order.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify stock restoration
    db_session.refresh(product)
    assert product.stock == 10  # Original stock

    # Verify order deletion
    response = await test_client.get(f"/orders/{order.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
