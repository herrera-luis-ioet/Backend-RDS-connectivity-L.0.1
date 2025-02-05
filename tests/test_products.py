"""Test module for product endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from tests.factories import ProductFactory


@pytest.mark.asyncio
async def test_create_product_success(test_client, db_session):
    """Test successful product creation."""
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 100
    }
    
    response = await test_client.post("/products/", json=product_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["description"] == product_data["description"]
    assert data["price"] == product_data["price"]
    assert data["stock"] == product_data["stock"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_product_validation(test_client):
    """Test product creation with invalid data."""
    invalid_products = [
        {
            "name": "",  # Empty name
            "description": "Test",
            "price": 10.0,
            "stock": 100
        },
        {
            "name": "Test",
            "description": "Test",
            "price": -10.0,  # Negative price
            "stock": 100
        },
        {
            "name": "Test",
            "description": "Test",
            "price": 10.0,
            "stock": -1  # Negative stock
        }
    ]
    
    for product_data in invalid_products:
        response = await test_client.post("/products/", json=product_data)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_product(test_client, db_session):
    """Test retrieving a specific product."""
    product = ProductFactory(session=db_session)
    
    response = await test_client.get(f"/products/{product.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == product.id
    assert data["name"] == product.name
    assert data["description"] == product.description
    assert data["price"] == product.price
    assert data["stock"] == product.stock
    
    # Test non-existent product
    response = await test_client.get("/products/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_products_pagination(test_client, db_session):
    """Test product listing with pagination."""
    # Create 15 products
    products = [ProductFactory(session=db_session) for _ in range(15)]
    
    # Test default pagination (limit=100)
    response = await test_client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 15
    
    # Test custom pagination
    response = await test_client.get("/products/?skip=5&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Verify correct products are returned
    product_ids = [p["id"] for p in data]
    expected_ids = [p.id for p in sorted(products, key=lambda x: x.id)[5:10]]
    assert product_ids == expected_ids


@pytest.mark.asyncio
async def test_update_product(test_client, db_session):
    """Test product update."""
    product = ProductFactory(session=db_session)
    
    update_data = {
        "name": "Updated Product",
        "price": 199.99
    }
    
    response = await test_client.put(f"/products/{product.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["price"] == update_data["price"]
    assert data["description"] == product.description  # Unchanged field
    assert data["stock"] == product.stock  # Unchanged field
    
    # Test non-existent product
    response = await test_client.put("/products/9999", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_product(test_client, db_session):
    """Test product deletion."""
    product = ProductFactory(session=db_session)
    
    response = await test_client.delete(f"/products/{product.id}")
    assert response.status_code == 204
    
    # Verify product is deleted
    response = await test_client.get(f"/products/{product.id}")
    assert response.status_code == 404
    
    # Test deleting non-existent product
    response = await test_client.delete("/products/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_updates(test_client, db_session):
    """Test concurrent product updates."""
    product = ProductFactory(session=db_session, stock=100)
    
    # Simulate concurrent stock updates
    update_data_1 = {"stock": 90}  # Decrease by 10
    update_data_2 = {"stock": 95}  # Decrease by 5
    
    response1 = await test_client.put(f"/products/{product.id}", json=update_data_1)
    response2 = await test_client.put(f"/products/{product.id}", json=update_data_2)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Get final state
    response = await test_client.get(f"/products/{product.id}")
    assert response.status_code == 200
    data = response.json()
    
    # Last update should win
    assert data["stock"] == 95