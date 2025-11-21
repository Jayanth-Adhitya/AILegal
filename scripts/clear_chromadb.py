#!/usr/bin/env python3
"""
Clear ChromaDB Collections

This script clears the ChromaDB vector store collections.
Use this to reset the policy embeddings database.

Usage:
    # Clear all collections
    python scripts/clear_chromadb.py

    # Clear specific collection
    python scripts/clear_chromadb.py --collection policies

    # Clear company-specific data (requires company_id)
    python scripts/clear_chromadb.py --company COMPANY_ID
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vector_store.embeddings import PolicyEmbeddings
from src.core.config import settings
import chromadb
from chromadb.config import Settings as ChromaSettings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clear_all_collections():
    """Clear all ChromaDB collections."""
    logger.info("Clearing all ChromaDB collections...")

    # Initialize ChromaDB client
    chroma_client = chromadb.PersistentClient(
        path=str(settings.chroma_db_path),
        settings=ChromaSettings(anonymized_telemetry=False)
    )

    # List all collections
    collections = chroma_client.list_collections()

    if not collections:
        logger.info("✅ No collections found. ChromaDB is already empty.")
        return

    logger.info(f"Found {len(collections)} collection(s): {[c.name for c in collections]}")

    # Delete each collection
    for collection in collections:
        logger.info(f"Deleting collection: {collection.name}")
        chroma_client.delete_collection(collection.name)

    logger.info("✅ All collections cleared successfully!")


def clear_policy_collection():
    """Clear the policies collection."""
    logger.info(f"Clearing policy collection: {settings.chroma_collection_name}")

    policy_embeddings = PolicyEmbeddings()
    policy_embeddings.clear_collection()

    logger.info("✅ Policy collection cleared successfully!")


def clear_company_policies(company_id: str):
    """
    Clear policies for a specific company.

    Args:
        company_id: Company ID to clear policies for
    """
    logger.info(f"Clearing policies for company: {company_id}")

    # Initialize ChromaDB client
    chroma_client = chromadb.PersistentClient(
        path=str(settings.chroma_db_path),
        settings=ChromaSettings(anonymized_telemetry=False)
    )

    # Get collection
    try:
        collection = chroma_client.get_collection(settings.chroma_collection_name)
    except Exception:
        logger.info("✅ Collection doesn't exist. Nothing to clear.")
        return

    # Get all documents for this company
    results = collection.get(
        where={"company_id": company_id},
        include=["metadatas"]
    )

    if not results["ids"]:
        logger.info(f"✅ No policies found for company {company_id}")
        return

    logger.info(f"Found {len(results['ids'])} policy chunks for company {company_id}")

    # Delete by IDs
    collection.delete(ids=results["ids"])

    logger.info(f"✅ Cleared {len(results['ids'])} policy chunks for company {company_id}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Clear ChromaDB collections")
    parser.add_argument(
        "--collection",
        choices=["policies", "all"],
        default="all",
        help="Which collection to clear (default: all)"
    )
    parser.add_argument(
        "--company",
        type=str,
        help="Clear policies for specific company ID only"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    # Confirmation
    if not args.confirm:
        if args.company:
            prompt = f"Clear all policies for company {args.company}? (yes/no): "
        elif args.collection == "all":
            prompt = "⚠️  Clear ALL ChromaDB collections? This cannot be undone! (yes/no): "
        else:
            prompt = f"Clear collection '{args.collection}'? (yes/no): "

        response = input(prompt).strip().lower()
        if response not in ["yes", "y"]:
            logger.info("Operation cancelled.")
            return

    try:
        if args.company:
            clear_company_policies(args.company)
        elif args.collection == "all":
            clear_all_collections()
        elif args.collection == "policies":
            clear_policy_collection()

        logger.info("\n✅ Operation completed successfully!")
        logger.info("💡 Remember to re-ingest your policies if needed.")

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
