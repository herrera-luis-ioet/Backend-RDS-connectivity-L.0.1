"""Integration tests for Product and Order Management API."""
import asyncio
import pytest
from fastapi import status
from product_order_api.schemas.order import OrderStatus
from tests.factories import ProductFactory, OrderFactory, OrderItemFactory


@pytest.mark.asyncio
async def test_complete_order_lifecycle(test_client, db_session):
    """Test complete order lifecycle from creation to completion."""
    # Create test products with initial stock
    product1 = ProductFactory(price=50.0, stock=10, session=db_session)
    product2 = ProductFactory(price=30.0, stock=15, session=db_session)

    # Create order
    order_data = {
        "customer_name": "Jane Smith",
        "customer_email": "jane@example.com",
        "items": [
            {"product_id": product1.id, "quantity": 2},
            {"product_id": product2.id, "quantity": 3}
        ]
    }

    # Step 1: Create order and verify initial state
    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_201_CREATED
    order_id = response.json()["id"]
    
    # Verify stock reduction
    db_session.refresh(product1)
    db_session.refresh(product2)
    assert product1.stock == 8  # 10 - 2
    assert product2.stock == 12  # 15 - 3

    # Step 2: Process order
    response = await test_client.put(
        f"/orders/{order_id}",
        json={"status": OrderStatus.PROCESSING}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == OrderStatus.PROCESSING

    # Step 3: Complete order
    response = await test_client.put(
        f"/orders/{order_id}",
        json={"status": OrderStatus.COMPLETED}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == OrderStatus.COMPLETED

    # Verify final state
    response = await test_client.get(f"/orders/{order_id}")
    order_data = response.json()
    assert order_data["status"] == OrderStatus.COMPLETED
    assert order_data["total_amount"] == (2 * 50.0 + 3 * 30.0)


@pytest.mark.asyncio
async def test_concurrent_order_processing(test_client, db_session):
    """Test concurrent order processing for the same product."""
    # Create product with limited stock
    product = ProductFactory(price=100.0, stock=10, session=db_session)
    db_session.commit()
    db_session.refresh(product)

    # Prepare concurrent orders
    order_data_1 = {
        "customer_name": "Customer 1",
        "customer_email": "customer1@example.com",
        "items": [{"product_id": product.id, "quantity": 6}]
    }
    order_data_2 = {
        "customer_name": "Customer 2",
        "customer_email": "customer2@example.com",
        "items": [{"product_id": product.id, "quantity": 5}]
    }

    # Create orders concurrently
    responses = await asyncio.gather(
        test_client.post("/orders/", json=order_data_1),
        test_client.post("/orders/", json=order_data_2)
    )

    # One order should succeed, one should fail due to insufficient stock
    success_count = sum(1 for r in responses if r.status_code == status.HTTP_201_CREATED)
    failure_count = sum(1 for r in responses if r.status_code == status.HTTP_400_BAD_REQUEST)
    
    assert success_count == 1
    assert failure_count == 1

    # Verify final stock
    db_session.refresh(product)
    assert product.stock == 4  # 10 - 6 (from successful order)


@pytest.mark.asyncio
async def test_order_cancellation_with_stock_management(test_client, db_session):
    """Test order cancellation and stock restoration."""
    # Create products
    products = [
        ProductFactory(price=75.0, stock=20, session=db_session),
        ProductFactory(price=45.0, stock=30, session=db_session)
    ]

    # Create order with multiple items
    order_data = {
        "customer_name": "Bob Wilson",
        "customer_email": "bob@example.com",
        "items": [
            {"product_id": products[0].id, "quantity": 5},
            {"product_id": products[1].id, "quantity": 8}
        ]
    }

    # Create and process order
    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_201_CREATED
    order_id = response.json()["id"]

    response = await test_client.put(
        f"/orders/{order_id}",
        json={"status": OrderStatus.PROCESSING}
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify initial stock reduction
    db_session.refresh(products[0])
    db_session.refresh(products[1])
    assert products[0].stock == 15  # 20 - 5
    assert products[1].stock == 22  # 30 - 8

    # Cancel order
    response = await test_client.put(
        f"/orders/{order_id}",
        json={"status": OrderStatus.CANCELLED}
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify stock restoration
    db_session.refresh(products[0])
    db_session.refresh(products[1])
    assert products[0].stock == 20  # Restored to original
    assert products[1].stock == 30  # Restored to original


@pytest.mark.asyncio
async def test_mixed_product_availability(test_client, db_session):
    """Test order creation with mixed product availability."""
    # Create products with different stock levels
    products = [
        ProductFactory(price=60.0, stock=5, session=db_session),   # Limited stock
        ProductFactory(price=40.0, stock=0, session=db_session),   # Out of stock
        ProductFactory(price=25.0, stock=100, session=db_session)  # Plenty of stock
    ]

    # Test order with out-of-stock product
    order_data = {
        "customer_name": "Alice Brown",
        "customer_email": "alice@example.com",
        "items": [
            {"product_id": products[0].id, "quantity": 2},
            {"product_id": products[1].id, "quantity": 1}  # Out of stock
        ]
    }

    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient stock" in response.json()["error"]["message"]

    # Verify no stock was modified
    for product in products:
        db_session.refresh(product)
    assert products[0].stock == 5
    assert products[1].stock == 0
    assert products[2].stock == 100

    # Test successful order with available products
    order_data = {
        "customer_name": "Alice Brown",
        "customer_email": "alice@example.com",
        "items": [
            {"product_id": products[0].id, "quantity": 2},
            {"product_id": products[2].id, "quantity": 5}
        ]
    }

    response = await test_client.post("/orders/", json=order_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Verify stock updates
    for product in products:
        db_session.refresh(product)
    assert products[0].stock == 3   # 5 - 2
    assert products[1].stock == 0   # Unchanged
    assert products[2].stock == 95  # 100 - 5


@pytest.mark.asyncio
async def test_order_deletion_cascade(test_client, db_session):
    """Test order deletion with associated items and stock restoration."""
    # Create products and order
    products = [
        ProductFactory(price=85.0, stock=50, session=db_session),
        ProductFactory(price=35.0, stock=75, session=db_session)
    ]

    order = OrderFactory(status=OrderStatus.PENDING, session=db_session)
    order_items = [
        OrderItemFactory(
            order=order,
            product=products[0],
            quantity=10,
            session=db_session
        ),
        OrderItemFactory(
            order=order,
            product=products[1],
            quantity=15,
            session=db_session
        )
    ]

    # Update stock to simulate order creation
    products[0].stock -= 10
    products[1].stock -= 15
    db_session.commit()

    # Delete order
    response = await test_client.delete(f"/orders/{order.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify stock restoration
    db_session.refresh(products[0])
    db_session.refresh(products[1])
    assert products[0].stock == 50  # Restored to original
    assert products[1].stock == 75  # Restored to original

    # Verify order and items are deleted
    response = await test_client.get(f"/orders/{order.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
