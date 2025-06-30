import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Event listeners for automatic timestamp handling
@event.listens_for(SQLModel, "before_insert", propagate=True)
def set_created_at(mapper, connection, target):
    """Set created_at timestamp before inserting"""
    from datetime import UTC, datetime

    if hasattr(target, "created_at") and target.created_at is None:
        target.created_at = datetime.now(UTC)
    if hasattr(target, "updated_at") and target.updated_at is None:
        target.updated_at = datetime.now(UTC)


@event.listens_for(SQLModel, "before_update", propagate=True)
def set_updated_at(mapper, connection, target):
    """Set updated_at timestamp before updating"""
    from datetime import UTC, datetime

    if hasattr(target, "updated_at"):
        target.updated_at = datetime.now(UTC)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
