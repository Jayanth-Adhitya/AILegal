"""Database engine and session management."""

import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Create SQLite engine with WAL mode for better concurrency
engine = create_engine(
    'sqlite:///legal_ai.db',
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL query logging
)

# Enable WAL mode for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables."""
    from .models import User, Session, AnalysisJob  # Import to register models

    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized successfully")
    logger.info(f"   Database file: legal_ai.db")
    logger.info(f"   Tables created: users, sessions, analysis_jobs")
