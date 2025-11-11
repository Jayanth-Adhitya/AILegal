#!/usr/bin/env python3
"""Initialize the SQLite database with all tables."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import init_db

if __name__ == "__main__":
    print("🔧 Initializing Legal AI database...")
    print()

    try:
        init_db()
        print()
        print("✅ Database initialization complete!")
        print()
        print("You can now start the application:")
        print("   uvicorn src.api:app --reload")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
