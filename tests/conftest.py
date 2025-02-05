"""Test configuration and fixtures for pytest."""
import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Set testing environment
os.environ["TESTING"] = "true"

from product_order_api.database import Base, get_db
from product_order_api.main import app
from product_order_api.models.product import Product
from product_order_api.models.order import Order, OrderItem
from tests.database import clear_database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine using SQLite in-memory database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Enable foreign key support for SQLite
    def _enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    event.listen(engine, 'connect', _enable_foreign_keys)
    
    yield engine
    
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    session = TestingSessionLocal()
    
    try:
        # Clear database before each test
        clear_database(session)
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
async def test_client(db_session, event_loop):
    """Create an async test client with database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()
