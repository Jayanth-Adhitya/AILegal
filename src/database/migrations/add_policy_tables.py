"""
Database migration: Add policy management tables

This migration adds three new tables:
1. policies - Core policy records with metadata
2. policy_sections - Individual sections within policies
3. policy_versions - Version history snapshots

Run with: python -m src.database.migrations.add_policy_tables
"""

from sqlalchemy import create_engine, text
from src.core.config import settings
from src.database.database import Base, engine
from src.database.models import Policy, PolicySection, PolicyVersion
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade():
    """Create policy tables."""
    logger.info("Running migration: add_policy_tables")

    try:
        # Create all tables defined in models
        logger.info("Creating policies table...")
        logger.info("Creating policy_sections table...")
        logger.info("Creating policy_versions table...")

        Base.metadata.create_all(bind=engine, checkfirst=True)

        logger.info("✓ Migration completed successfully")
        logger.info("  - policies table created")
        logger.info("  - policy_sections table created")
        logger.info("  - policy_versions table created")
        logger.info("  - All indexes and foreign keys created")

    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        raise


def downgrade():
    """Drop policy tables."""
    logger.info("Rolling back migration: add_policy_tables")

    try:
        with engine.connect() as conn:
            # Drop in reverse order due to foreign keys
            logger.info("Dropping policy_versions table...")
            conn.execute(text("DROP TABLE IF EXISTS policy_versions CASCADE"))

            logger.info("Dropping policy_sections table...")
            conn.execute(text("DROP TABLE IF EXISTS policy_sections CASCADE"))

            logger.info("Dropping policies table...")
            conn.execute(text("DROP TABLE IF EXISTS policies CASCADE"))

            conn.commit()

        logger.info("✓ Rollback completed successfully")

    except Exception as e:
        logger.error(f"✗ Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
