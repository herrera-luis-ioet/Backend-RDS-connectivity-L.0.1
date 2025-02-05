"""Database configuration module for Amazon RDS MySQL connection."""
import os
from dotenv import load_dotenv
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool


# PUBLIC_INTERFACE
Base = declarative_base()
load_dotenv()

def get_database_url() -> str:
    """
    Construct database URL from environment variables.

    Returns:
        str: The database URL for SQLAlchemy
    """
    # Use SQLite for testing
    if os.getenv("TESTING", "false").lower() == "true":
        return "sqlite:///:memory:"

    # Use MySQL for production
    db_user = os.getenv("DB_USER", "admin")
    db_password = os.getenv("DB_PASSWORD", "password")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "product_order_db")
    print("AQUi",db_user, db_password, db_host)
    return (
        f"mysql+pymysql://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )


# Configure SQLAlchemy engine
def get_engine_config():
    """Get database engine configuration based on environment."""
    is_testing = os.getenv("TESTING", "false").lower() == "true"
    
    if is_testing:
        return {
            "connect_args": {"check_same_thread": False},
            "echo": False
        }
    
    return {
        "poolclass": QueuePool,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "echo": False
    }

engine = create_engine(get_database_url(), **get_engine_config())


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """
    Get database session from the connection pool.

    Yields:
        Session: SQLAlchemy session object

    Raises:
        SQLAlchemyError: If there's an issue with the database connection
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    finally:
        db.close()


# PUBLIC_INTERFACE
def init_db() -> None:
    """
    Initialize database by creating all tables.

    This function should be called when the application starts.
    """
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        raise Exception(f"Failed to initialize database: {str(e)}")
