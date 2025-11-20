"""
Migration: Add source field to analysis_jobs table

This migration adds the 'source' column to track whether analysis
came from web upload or Word add-in.
"""

import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def migrate_add_source_field(db_path: str = "legal_ai.db"):
    """
    Add source field to analysis_jobs table.

    Args:
        db_path: Path to SQLite database file
    """
    db_file = Path(db_path)

    if not db_file.exists():
        logger.warning(f"Database file not found: {db_path}. Creating new database.")
        db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(analysis_jobs)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'source' in columns:
            logger.info("Column 'source' already exists in analysis_jobs table. Skipping migration.")
            return

        # Add source column with default value
        logger.info("Adding 'source' column to analysis_jobs table...")
        cursor.execute("""
            ALTER TABLE analysis_jobs
            ADD COLUMN source TEXT NOT NULL DEFAULT 'web_upload'
        """)

        # Create index on source field
        logger.info("Creating index on source column...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_jobs_source
            ON analysis_jobs(source)
        """)

        # Create composite index for user_id + created_at (for history queries)
        logger.info("Creating composite index for history queries...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_jobs_user_created
            ON analysis_jobs(user_id, created_at DESC)
        """)

        conn.commit()
        logger.info("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_add_source_field()
