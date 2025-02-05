"""Test database utilities."""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from product_order_api.database import Base


def clear_database(session: Session) -> None:
    """Clear all data from database tables."""
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


@contextmanager
def transaction(session: Session) -> Generator[Session, None, None]:
    """
    Transaction context manager for tests.
    
    Provides automatic rollback after each test to ensure isolation.
    """
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()