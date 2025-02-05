"""Product router module."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.database import get_db
from src.errors import (
    ResourceNotFoundError,
    DatabaseError
)
from src.models.product import Product
from src.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)


# Create router instance
router = APIRouter(
    prefix="/products",
    tags=["products"]
)


# PUBLIC_INTERFACE
@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List all products",
    description="Get a paginated list of all products in the system",
    responses={
        200: {
            "description": "List of products retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Product 1",
                            "description": "Description of product 1",
                            "price": 29.99,
                            "stock": 100
                        },
                        {
                            "id": 2,
                            "name": "Product 2",
                            "description": "Description of product 2",
                            "price": 49.99,
                            "stock": 50
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Database error occurred",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error listing products: Database connection failed"
                    }
                }
            }
        }
    }
)
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Product]:
    """
    Get a list of all products with pagination.

    Args:
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        db (Session): Database session

    Returns:
        List[Product]: List of products
    """
    try:
        products = db.query(Product).offset(skip).limit(limit).all()
        return products
    except SQLAlchemyError as e:
        raise DatabaseError(f"Error listing products: {str(e)}")


# PUBLIC_INTERFACE
@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a specific product",
    description="Get detailed information about a specific product by its ID",
    responses={
        200: {
            "description": "Product found and returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Sample Product",
                        "description": "Detailed description of the product",
                        "price": 29.99,
                        "stock": 100
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
        500: {
            "description": "Database error occurred",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error retrieving product: Database error"
                    }
                }
            }
        }
    }
)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
) -> Product:
    """
    Get a specific product by ID.

    Args:
        product_id (int): Product ID
        db (Session): Database session

    Returns:
        Product: Product details

    Raises:
        HTTPException: If product is not found
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ResourceNotFoundError("Product", product_id)
        return product
    except SQLAlchemyError as e:
        raise DatabaseError(f"Error retrieving product: {str(e)}")


# PUBLIC_INTERFACE
@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product with the provided details",
    responses={
        201: {
            "description": "Product created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "New Product",
                        "description": "Description of new product",
                        "price": 39.99,
                        "stock": 150
                    }
                }
            }
        },
        500: {
            "description": "Database error occurred",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error creating product: Database error"
                    }
                }
            }
        }
    }
)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
) -> Product:
    """
    Create a new product.

    Args:
        product (ProductCreate): Product data
        db (Session): Database session

    Returns:
        Product: Created product details
    """
    try:
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Error creating product: {str(e)}")


# PUBLIC_INTERFACE
@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db)
) -> Product:
    """
    Update a product.

    Args:
        product_id (int): Product ID
        product (ProductUpdate): Updated product data
        db (Session): Database session

    Returns:
        Product: Updated product details

    Raises:
        HTTPException: If product is not found
    """
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            raise ResourceNotFoundError("Product", product_id)

        update_data = product.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)

        db.commit()
        db.refresh(db_product)
        return db_product
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Error updating product: {str(e)}")


# PUBLIC_INTERFACE
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a product.

    Args:
        product_id (int): Product ID
        db (Session): Database session

    Raises:
        HTTPException: If product is not found
    """
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            raise ResourceNotFoundError("Product", product_id)

        db.delete(db_product)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Error deleting product: {str(e)}")
