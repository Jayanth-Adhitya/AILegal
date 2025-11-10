"""Script to ingest policies and laws into ChromaDB vector store."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.vector_store.embeddings import PolicyEmbeddings
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to ingest policies."""
    print("=" * 60)
    print("AI Legal Assistant - Policy Ingestion")
    print("=" * 60)
    print()

    # Check if policy directories exist
    policies_dir = Path("data/policies")
    laws_dir = Path("data/laws")

    if not policies_dir.exists():
        print(f"❌ Policies directory not found: {policies_dir}")
        print("   Create the directory and add your policy files (.txt or .md)")
        return

    if not laws_dir.exists():
        print(f"⚠️  Laws directory not found: {laws_dir}")
        print("   Creating directory...")
        laws_dir.mkdir(parents=True, exist_ok=True)

    # Count files
    policy_files = list(policies_dir.glob("*.txt")) + list(policies_dir.glob("*.md"))
    law_files = list(laws_dir.glob("*.txt")) + list(laws_dir.glob("*.md"))

    print(f"📁 Found {len(policy_files)} policy files in {policies_dir}")
    print(f"📁 Found {len(law_files)} law files in {laws_dir}")
    print()

    if len(policy_files) == 0 and len(law_files) == 0:
        print("❌ No policy or law files found!")
        print()
        print("Add .txt or .md files to:")
        print(f"  - {policies_dir.absolute()}")
        print(f"  - {laws_dir.absolute()}")
        print()
        print("Example file naming: Legal_Liability_v1.0.txt")
        return

    # Initialize embeddings
    print("🚀 Initializing PolicyEmbeddings...")
    try:
        embeddings = PolicyEmbeddings()
        print("✅ PolicyEmbeddings initialized")
        print()
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        print()
        print("Make sure your GOOGLE_API_KEY is set in .env file")
        return

    # Check if collection already has data
    stats = embeddings.get_collection_stats()
    if stats["total_documents"] > 0:
        print(f"⚠️  Collection already contains {stats['total_documents']} documents")
        response = input("Clear and re-ingest? (yes/no): ").strip().lower()
        if response == "yes":
            print("🗑️  Clearing collection...")
            embeddings.clear_collection()
            embeddings = PolicyEmbeddings()  # Reinitialize
            print("✅ Collection cleared")
            print()

    # Ingest policies
    print("📥 Starting ingestion...")
    print()

    try:
        results = embeddings.ingest_policies()

        print()
        print("=" * 60)
        print("✅ Ingestion Complete!")
        print("=" * 60)
        print()
        print(f"📊 Results:")
        print(f"   - Policies ingested: {results['policies']} chunks")
        print(f"   - Laws ingested: {results['laws']} chunks")
        print(f"   - Total: {sum(results.values())} chunks")
        print()

        # Get final stats
        final_stats = embeddings.get_collection_stats()
        print(f"📈 Vector Store Stats:")
        print(f"   - Collection: {final_stats['collection_name']}")
        print(f"   - Total documents: {final_stats['total_documents']}")
        print(f"   - Embedding model: {final_stats['embedding_model']}")
        print()

        print("✅ Ready to analyze contracts!")
        print()

    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
