#!/usr/bin/env python3
"""Backup the SQLite database."""

import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    """Create a timestamped backup of the database."""
    db_file = Path("legal_ai.db")

    if not db_file.exists():
        print("❌ Database file not found: legal_ai.db")
        return False

    # Create backups directory
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"legal_ai_backup_{timestamp}.db"

    try:
        shutil.copy2(db_file, backup_file)
        print(f"✅ Database backed up successfully:")
        print(f"   {backup_file}")

        # Show backup size
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        print(f"   Size: {size_mb:.2f} MB")

        return True

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Backing up Legal AI database...")
    print()
    backup_database()
