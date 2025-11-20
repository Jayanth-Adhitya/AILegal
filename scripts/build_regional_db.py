#!/usr/bin/env python3
"""
Pre-build regional knowledge bases before deployment.

This script ingests all regional documents into ChromaDB once,
allowing you to package the pre-built database in your Docker image.

Usage:
    python scripts/build_regional_db.py

    # Custom batch size and delay (for rate limiting)
    python scripts/build_regional_db.py --batch-size 25 --delay 2.0

After running:
    - ChromaDB data is saved to ./chroma_db/
    - You can package this directory in Docker
    - Source documents in data/regional/ are no longer needed for deployment

Rate Limiting:
    - Gemini embedding API has rate limits (1500 RPM for free tier)
    - This script uses batching and exponential backoff to handle limits
    - Adjust --batch-size and --delay if you hit rate limits
"""

import sys
import logging
import time
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings, REGION_CONFIG, get_enabled_regions
from src.vector_store.embeddings import PolicyEmbeddings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_regional_databases(batch_size: int = None, delay: float = None):
    """
    Pre-build all regional knowledge bases.

    Args:
        batch_size: Number of chunks to embed per batch (default: from settings)
        delay: Delay in seconds between batches (default: from settings)
    """
    logger.info("=" * 80)
    logger.info("🔨 Building Regional Knowledge Bases")
    logger.info("=" * 80)

    # Override settings with command line arguments if provided
    if batch_size is not None:
        settings.embedding_batch_size = batch_size
    if delay is not None:
        settings.embedding_delay_seconds = delay

    # Display rate limiting configuration
    logger.info(f"⚙️  Rate Limiting Configuration:")
    logger.info(f"   - Batch size: {settings.embedding_batch_size} chunks per batch")
    logger.info(f"   - Delay: {settings.embedding_delay_seconds}s between batches")
    logger.info(f"   - Max RPM: {settings.embedding_requests_per_minute}")
    logger.info(f"   - Retry attempts: 5 (with exponential backoff)")
    logger.info(f"   - Estimated time for 300 chunks: ~{(300 / settings.embedding_batch_size) * settings.embedding_delay_seconds:.1f}s")
    print()

    if not settings.regional_kb_enabled:
        logger.warning("⚠️  Regional KB is disabled in configuration")
        return

    enabled_regions = get_enabled_regions()

    if not enabled_regions:
        logger.warning("⚠️  No regions enabled in configuration")
        return

    logger.info(f"📋 Regions to build: {', '.join(enabled_regions)}")
    print()

    embeddings = PolicyEmbeddings()
    total_chunks = 0

    for region_code in enabled_regions:
        region_config = REGION_CONFIG[region_code]
        data_dir = region_config["data_directory"]

        logger.info(f"🌍 Building region: {region_code}")
        logger.info(f"   Name: {region_config['metadata']['region_name']}")
        logger.info(f"   Data directory: {data_dir}")

        try:
            # Check if directory exists
            if not Path(data_dir).exists():
                logger.error(f"   ❌ Directory not found: {data_dir}")
                continue

            # Check if directory has documents
            doc_files = list(Path(data_dir).glob("*.pdf")) + \
                       list(Path(data_dir).glob("*.txt")) + \
                       list(Path(data_dir).glob("*.md")) + \
                       list(Path(data_dir).glob("*.docx"))

            if not doc_files:
                logger.warning(f"   ⚠️  No documents found in {data_dir}")
                continue

            logger.info(f"   📄 Found {len(doc_files)} documents")

            # Ingest documents
            chunks_ingested = embeddings.ingest_regional_directory(
                region_code=region_code,
                directory_path=data_dir
            )

            if chunks_ingested > 0:
                logger.info(f"   ✅ Ingested {chunks_ingested} chunks")
                total_chunks += chunks_ingested
            else:
                logger.info(f"   ℹ️  Region already built (skipped)")

        except Exception as e:
            logger.error(f"   ❌ Error building region {region_code}: {e}")
            continue

        print()

    # Display summary
    logger.info("=" * 80)
    logger.info(f"✅ Build Complete!")
    logger.info(f"   Total chunks ingested: {total_chunks}")
    logger.info(f"   Database location: {settings.chroma_db_path}")
    logger.info("=" * 80)
    print()

    # Display collection stats
    logger.info("📊 Collection Statistics:")
    stats = embeddings.get_all_collection_stats()

    for collection_name, count in stats.items():
        logger.info(f"   {collection_name}: {count:,} documents")

    print()
    logger.info("🚀 Next Steps:")
    logger.info("   1. Verify the database works: python scripts/test_regional_retrieval.py")
    logger.info("   2. Package in Docker: COPY ./chroma_db /app/chroma_db")
    logger.info("   3. Deploy without source documents (data/regional/ not needed)")
    print()


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Pre-build regional knowledge bases for deployment"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help=f"Number of chunks per batch (default: {settings.embedding_batch_size})"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help=f"Delay in seconds between batches (default: {settings.embedding_delay_seconds})"
    )

    args = parser.parse_args()

    try:
        build_regional_databases(
            batch_size=args.batch_size,
            delay=args.delay
        )
    except KeyboardInterrupt:
        logger.info("\n⚠️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Build failed: {e}", exc_info=True)
        sys.exit(1)
