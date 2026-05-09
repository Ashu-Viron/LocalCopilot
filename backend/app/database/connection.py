"""Database connection configuration for Neon Postgres."""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.utils.logger import logger

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Create engine with connection pooling disabled for serverless
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Recommended for serverless/Neon
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from app.database.models import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
