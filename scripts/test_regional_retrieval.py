#!/usr/bin/env python3
"""
Test regional knowledge base retrieval.

This script verifies that the pre-built regional databases work correctly.

Usage:
    python scripts/test_regional_retrieval.py
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings, get_enabled_regions
from src.vector_store.retriever import PolicyRetriever
from src.vector_store.embeddings import PolicyEmbeddings
from src.services.geolocation_service import get_geo_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_regional_retrieval():
    """Test regional knowledge base retrieval."""
    logger.info("=" * 80)
    logger.info("🧪 Testing Regional Knowledge Base Retrieval")
    logger.info("=" * 80)
    print()

    # Test 1: Check collection stats
    logger.info("📊 Test 1: Checking collection statistics...")
    embeddings = PolicyEmbeddings()
    stats = embeddings.get_all_collection_stats()

    for collection_name, count in stats.items():
        status = "✅" if count > 0 else "❌"
        logger.info(f"   {status} {collection_name}: {count:,} documents")

    print()

    # Test 2: Test IP geolocation
    logger.info("🌍 Test 2: Testing IP-based region detection...")
    geo_service = get_geo_service()

    test_ips = [
        ("5.1.83.46", "AE", "dubai_uae"),  # UAE IP
        ("8.8.8.8", "US", None),            # US IP (no regional KB)
        ("invalid", None, None)             # Invalid IP
    ]

    for ip, expected_country, expected_region in test_ips:
        country = geo_service.get_country_from_ip(ip)
        region = geo_service.get_region_from_ip(ip)

        country_match = "✅" if country == expected_country else "❌"
        region_match = "✅" if region == expected_region else "❌"

        logger.info(f"   IP: {ip}")
        logger.info(f"      {country_match} Country: {country} (expected: {expected_country})")
        logger.info(f"      {region_match} Region: {region} (expected: {expected_region})")

    print()

    # Test 3: Test regional retrieval
    logger.info("🔍 Test 3: Testing regional document retrieval...")
    retriever = PolicyRetriever()

    # Multiple test queries to evaluate retrieval quality
    test_queries = [
        "payment terms and liability limitations",
        "intellectual property and copyright assignment",
        "termination clauses and agreement cancellation",
        "Dubai commercial law and regulations",
        "distribution agreement terms"
    ]

    # Test only if Dubai KB exists
    if "policies_dubai_uae" in stats and stats["policies_dubai_uae"] > 0:
        for test_query in test_queries:
            logger.info("=" * 80)
            logger.info(f"   📝 Query: '{test_query}'")

            # Retrieve from Dubai KB
            regional_results = retriever.retrieve_with_region(
                query=test_query,
                region_code="dubai_uae",
                n_results=5
            )

            if regional_results:
                logger.info(f"   ✅ Found {len(regional_results)} relevant documents")

                # Count by source
                regional_count = sum(1 for r in regional_results if r["metadata"].get("source_type") == "regional")
                logger.info(f"      - {regional_count} from Dubai KB")
                logger.info(f"      - {len(regional_results) - regional_count} from Global KB")

                # Show the retrieved documents
                logger.info("\n   📄 Retrieved Documents:")
                for i, result in enumerate(regional_results, 1):
                    metadata = result.get("metadata", {})
                    # Use similarity_score as the relevance score
                    score = result.get("similarity_score", result.get("weighted_score", 0.0))
                    # The text content is in the 'content' key
                    text_content = result.get("content", "No content found")
                    text_preview = text_content[:400] + "..." if len(text_content) > 400 else text_content

                    logger.info(f"\n   🔍 Result {i}:")
                    logger.info(f"      📊 Similarity Score: {score:.4f}")
                    logger.info(f"      📁 Source: {metadata.get('source_type', 'unknown').upper()}")
                    logger.info(f"      📄 File: {metadata.get('file_name', 'unknown')}")
                    if metadata.get('section_title'):
                        logger.info(f"      📌 Section: {metadata.get('section_title')}")
                    logger.info(f"      📖 Content Preview:")

                    # Format the preview text nicely
                    import textwrap
                    wrapped_text = textwrap.fill(text_preview, width=70, initial_indent="         ", subsequent_indent="         ")
                    logger.info(wrapped_text)
                    logger.info("      " + "-" * 70)
            else:
                logger.info("   ❌ No documents found for this query")

            print()  # Space between queries
    else:
        logger.warning("   ⚠️  Dubai KB not found, skipping regional test")

    print()

    # Summary
    logger.info("=" * 80)
    logger.info("✅ All tests completed!")
    logger.info("=" * 80)
    print()


if __name__ == "__main__":
    try:
        test_regional_retrieval()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
