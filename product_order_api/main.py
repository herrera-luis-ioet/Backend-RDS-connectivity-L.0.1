from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from src.database import init_db
from src.routers import products, orders
from src.errors import (
    APIError,
    api_error_handler,
    sqlalchemy_error_handler,
    generic_exception_handler
)


app = FastAPI(
    title="Product and Order Management API",
    description="""
    A comprehensive RESTful API for managing products and orders with MySQL RDS backend.
    
    ## Features
    * Product Management: Create, read, update, and delete products
    * Order Management: Place orders, track status, and manage order lifecycle
    * Inventory Control: Automatic stock management with order processing
    * Error Handling: Comprehensive error responses with detailed messages
    
    ## Authentication
    Currently, the API is open and does not require authentication.
    
    ## Rate Limiting
    No rate limiting is currently implemented.
    """,
    version="0.1.0",
    openapi_tags=[
        {
            "name": "products",
            "description": "Operations with products, including inventory management"
        },
        {
            "name": "orders",
            "description": "Operations with orders, including order placement and status management"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add exception handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/")
async def root():
    return {"message": "Welcome to Product and Order Management API"}


@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup."""
    init_db()
