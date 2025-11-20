#!/usr/bin/env python3
"""
Apply database schema migrations for document workflow.

This script adds missing columns to the documents table for:
- Document versioning
- Approval workflow
- E-signature support

Safe to run multiple times - only adds columns if they don't exist.
"""

import sys
import sqlite3
from pathlib import Path

def get_db_path():
    """Get database path from environment or use default."""
    import os

    # Check environment variable
    db_path = os.getenv("DATABASE_PATH")
    if db_path:
        return db_path

    # Check common locations
    locations = [
        "/app/data/legal_ai.db",  # Docker production
        "data/legal_ai.db",       # Docker local mount
        "Data/legal_assistant.db", # Old location
        "legal_ai.db",            # Current directory
    ]

    for loc in locations:
        if Path(loc).exists():
            return loc

    # Default to production path
    return "/app/data/legal_ai.db"


def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_column_if_not_exists(cursor, table_name, column_name, column_type):
    """Add a column to a table if it doesn't already exist."""
    if not column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            print(f"  ✓ Added column: {column_name}")
            return True
        except sqlite3.OperationalError as e:
            print(f"  ⚠ Error adding {column_name}: {e}")
            return False
    else:
        print(f"  - Column already exists: {column_name}")
        return False


def apply_migrations():
    """Apply all schema migrations."""
    db_path = get_db_path()

    print("=" * 60)
    print("Database Schema Migration")
    print("=" * 60)
    print(f"Database: {db_path}")
    print()

    if not Path(db_path).exists():
        print(f"⚠ Database not found at {db_path}")
        print("Database will be created on first API startup.")
        return True

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if documents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        if not cursor.fetchone():
            print("⚠ Documents table doesn't exist yet - will be created on first API startup")
            conn.close()
            return True

        print("📋 Applying migrations to 'documents' table...")
        print()

        added_count = 0

        # Document versioning columns
        print("1. Document Versioning:")
        added_count += add_column_if_not_exists(cursor, "documents", "version_number", "INTEGER DEFAULT 1")
        added_count += add_column_if_not_exists(cursor, "documents", "edited_by", "VARCHAR(36)")
        added_count += add_column_if_not_exists(cursor, "documents", "edited_at", "TIMESTAMP")
        added_count += add_column_if_not_exists(cursor, "documents", "is_locked", "BOOLEAN DEFAULT 0")
        added_count += add_column_if_not_exists(cursor, "documents", "lock_reason", "VARCHAR(255)")
        print()

        # Content storage columns
        print("2. Content Storage:")
        added_count += add_column_if_not_exists(cursor, "documents", "original_content", "TEXT")
        added_count += add_column_if_not_exists(cursor, "documents", "redlined_content", "TEXT")
        added_count += add_column_if_not_exists(cursor, "documents", "filename", "VARCHAR(255)")
        print()

        # Approval workflow columns
        print("3. Approval Workflow:")
        added_count += add_column_if_not_exists(cursor, "documents", "approval_status", "VARCHAR(50) DEFAULT 'pending'")
        added_count += add_column_if_not_exists(cursor, "documents", "all_parties_approved", "BOOLEAN DEFAULT 0")
        print()

        # E-signature columns
        print("4. E-Signature Support:")
        added_count += add_column_if_not_exists(cursor, "documents", "signature_status", "VARCHAR(50) DEFAULT 'not_started'")
        added_count += add_column_if_not_exists(cursor, "documents", "signatures_required", "INTEGER DEFAULT 0")
        added_count += add_column_if_not_exists(cursor, "documents", "signatures_completed", "INTEGER DEFAULT 0")
        added_count += add_column_if_not_exists(cursor, "documents", "fully_signed_at", "TIMESTAMP")
        print()

        # Commit changes
        conn.commit()
        conn.close()

        print("=" * 60)
        if added_count > 0:
            print(f"✅ Migration complete! Added {added_count} columns.")
        else:
            print("✅ Schema is up to date. No changes needed.")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = apply_migrations()
    sys.exit(0 if success else 1)
