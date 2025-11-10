"""Test script to verify setup without requiring policy ingestion."""

import sys
from pathlib import Path

print("=" * 70)
print("🔍 AI Legal Assistant - Setup Verification")
print("=" * 70)
print()

# Check 1: Python version
print("1️⃣ Checking Python version...")
import sys
version = sys.version_info
if version.major == 3 and version.minor >= 9:
    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
else:
    print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.9+)")
print()

# Check 2: Dependencies
print("2️⃣ Checking dependencies...")
dependencies = [
    "langchain",
    "langchain_google_genai",
    "chromadb",
    "docx",
    "fastapi",
    "pydantic"
]

all_deps_ok = True
for dep in dependencies:
    try:
        if dep == "docx":
            __import__("docx")
        else:
            __import__(dep)
        print(f"   ✅ {dep}")
    except ImportError:
        print(f"   ❌ {dep} (not installed)")
        all_deps_ok = False

print()

# Check 3: Configuration
print("3️⃣ Checking configuration...")
try:
    from src.core.config import settings

    if settings.google_api_key and settings.google_api_key != "your_gemini_api_key_here":
        print(f"   ✅ API key configured (starts with: {settings.google_api_key[:20]}...)")
    else:
        print("   ❌ API key not configured in .env file")
        all_deps_ok = False

    print(f"   ✅ Model: {settings.gemini_model}")
    print(f"   ✅ Embedding: {settings.embedding_model}")
except Exception as e:
    print(f"   ❌ Configuration error: {e}")
    all_deps_ok = False

print()

# Check 4: Data directories
print("4️⃣ Checking data directories...")
dirs = ["data/policies", "data/laws", "data/uploads", "data/outputs", "data/chroma_db"]
for dir_path in dirs:
    if Path(dir_path).exists():
        print(f"   ✅ {dir_path}")
    else:
        print(f"   ❌ {dir_path} (missing)")

print()

# Check 5: Sample policies
print("5️⃣ Checking sample policies...")
policy_dir = Path("data/policies")
if policy_dir.exists():
    policy_files = list(policy_dir.glob("*.txt"))
    if len(policy_files) > 0:
        print(f"   ✅ Found {len(policy_files)} policy files")
        for pf in policy_files:
            print(f"      - {pf.name}")
    else:
        print("   ⚠️  No policy files found")
else:
    print("   ❌ Policy directory missing")

print()

# Check 6: ChromaDB collection
print("6️⃣ Checking ChromaDB collection...")
try:
    from src.vector_store.embeddings import PolicyEmbeddings
    embeddings = PolicyEmbeddings()
    stats = embeddings.get_collection_stats()

    if stats["total_documents"] > 0:
        print(f"   ✅ Collection exists with {stats['total_documents']} documents")
    else:
        print("   ⚠️  Collection exists but is empty")
        print("      Run: python -m src.scripts.ingest_policies")
except Exception as e:
    print(f"   ⚠️  Collection not initialized: {e}")
    print("      Run: python -m src.scripts.ingest_policies")

print()

# Check 7: Test Gemini API
print("7️⃣ Testing Gemini API connection...")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from src.core.config import settings

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0.1
    )

    response = llm.invoke("Say 'API test successful' in exactly those words.")

    if "successful" in response.content.lower():
        print(f"   ✅ Gemini API working!")
        print(f"      Response: {response.content[:50]}...")
    else:
        print(f"   ⚠️  API responded but unexpected output")

except Exception as e:
    print(f"   ❌ API test failed: {e}")
    all_deps_ok = False

print()
print("=" * 70)

if all_deps_ok:
    print("✅ Setup Complete! System is ready.")
    print()
    print("Next steps:")
    print("1. If collection is empty, run: python -m src.scripts.ingest_policies")
    print("2. Test clause analysis: python main.py clause \"test clause text\"")
    print("3. Start API: python -m uvicorn src.api:app --reload")
else:
    print("⚠️  Some issues detected. Fix the items marked with ❌ above.")
    print()
    print("Common fixes:")
    print("- Missing dependencies: pip install -r requirements.txt")
    print("- Missing API key: Add GOOGLE_API_KEY to .env file")
    print("- Empty collection: Run python -m src.scripts.ingest_policies")

print("=" * 70)
