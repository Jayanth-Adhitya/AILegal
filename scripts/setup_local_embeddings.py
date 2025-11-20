#!/usr/bin/env python3
"""
Setup script for local embeddings.

This script helps you set up local embedding models to avoid API quotas.

Usage:
    python scripts/setup_local_embeddings.py

Options:
    --model: Choose embedding model (default: all-MiniLM-L6-v2)
    --skip-download: Skip model pre-download
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_dependencies():
    """Check if required packages are installed."""
    print("🔍 Checking dependencies...")

    try:
        import torch
        print(f"   ✅ PyTorch installed (version: {torch.__version__})")

        # Check for GPU
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"   🚀 GPU detected: {gpu_name}")
        else:
            print(f"   🖥️  CPU mode (no GPU detected)")

    except ImportError:
        print("   ❌ PyTorch not installed")
        print("\n📦 Installing PyTorch...")
        os.system("pip install torch")

    try:
        import sentence_transformers
        print(f"   ✅ sentence-transformers installed (version: {sentence_transformers.__version__})")
    except ImportError:
        print("   ❌ sentence-transformers not installed")
        print("\n📦 Installing sentence-transformers...")
        os.system("pip install sentence-transformers transformers")

    try:
        import transformers
        print(f"   ✅ transformers installed (version: {transformers.__version__})")
    except ImportError:
        print("   ❌ transformers not installed")
        print("\n📦 Installing transformers...")
        os.system("pip install transformers")

    print()


def download_model(model_name: str):
    """Pre-download the embedding model."""
    print(f"📥 Downloading embedding model: {model_name}")
    print("   This may take 1-2 minutes on first run...")
    print()

    try:
        from sentence_transformers import SentenceTransformer

        # Download model
        model = SentenceTransformer(model_name)

        # Test embedding
        test_text = "This is a test sentence."
        embedding = model.encode(test_text)

        print(f"   ✅ Model downloaded successfully!")
        print(f"   📊 Embedding dimension: {len(embedding)}")
        print(f"   📁 Cached at: ~/.cache/huggingface/hub/")
        print()

        return True

    except Exception as e:
        print(f"   ❌ Failed to download model: {e}")
        return False


def update_env_file(model_name: str):
    """Update .env file with local embedding settings."""
    env_path = Path(".env")

    print("📝 Updating .env file...")

    # Read existing .env
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    # Update or add settings
    updated = False
    local_model_updated = False

    new_lines = []
    for line in lines:
        if line.startswith("USE_LOCAL_EMBEDDINGS="):
            new_lines.append("USE_LOCAL_EMBEDDINGS=true\n")
            updated = True
        elif line.startswith("LOCAL_EMBEDDING_MODEL="):
            new_lines.append(f"LOCAL_EMBEDDING_MODEL={model_name}\n")
            local_model_updated = True
        else:
            new_lines.append(line)

    # Add if not present
    if not updated:
        new_lines.append("\n# Local Embeddings (no API limits!)\n")
        new_lines.append("USE_LOCAL_EMBEDDINGS=true\n")

    if not local_model_updated:
        new_lines.append(f"LOCAL_EMBEDDING_MODEL={model_name}\n")

    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)

    print(f"   ✅ Updated {env_path}")
    print(f"   USE_LOCAL_EMBEDDINGS=true")
    print(f"   LOCAL_EMBEDDING_MODEL={model_name}")
    print()


def check_existing_database():
    """Check if there's an existing database that needs to be rebuilt."""
    db_path = Path("data/chroma_db")

    if db_path.exists():
        print("⚠️  Warning: Existing ChromaDB database found!")
        print()
        print("   You need to rebuild the database with local embeddings.")
        print("   API-based and local embeddings are NOT compatible.")
        print()
        response = input("   Delete existing database and rebuild? [y/N]: ")

        if response.lower() == 'y':
            import shutil
            print(f"   🗑️  Deleting {db_path}...")
            shutil.rmtree(db_path)
            print(f"   ✅ Database deleted")
            return True
        else:
            print("   ℹ️  Keeping existing database")
            print("   You can manually delete it later: rm -rf data/chroma_db/")
            return False
    else:
        print("✅ No existing database found (fresh setup)")
        return True


def main():
    """Main setup flow."""
    parser = argparse.ArgumentParser(description="Setup local embeddings")
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model to use"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip model pre-download"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("🚀 Local Embeddings Setup")
    print("=" * 80)
    print()

    # Step 1: Check dependencies
    check_dependencies()

    # Step 2: Check existing database
    can_rebuild = check_existing_database()
    print()

    # Step 3: Download model
    if not args.skip_download:
        success = download_model(args.model)
        if not success:
            print("❌ Setup failed: Could not download model")
            sys.exit(1)

    # Step 4: Update .env
    update_env_file(args.model)

    # Step 5: Instructions
    print("=" * 80)
    print("✅ Setup Complete!")
    print("=" * 80)
    print()
    print("📋 Next Steps:")
    print()

    if can_rebuild:
        print("   1. Build the database with local embeddings:")
        print("      python scripts/build_regional_db.py")
        print()
        print("   2. Expected time:")
        print("      - ~1-2 minutes on CPU")
        print("      - ~10-30 seconds on GPU")
        print()
        print("   3. No API limits, completely free! 🎉")
    else:
        print("   1. Delete the old database:")
        print("      rm -rf data/chroma_db/")
        print()
        print("   2. Build the database with local embeddings:")
        print("      python scripts/build_regional_db.py")

    print()
    print("📚 For more information, see: docs/LOCAL_EMBEDDINGS.md")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
