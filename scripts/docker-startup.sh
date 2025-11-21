#!/bin/bash
set -e

echo "=== AI Contract Assistant Startup ==="

# Apply database schema migrations
echo "📋 Checking database schema..."
python scripts/apply_schema_migrations.py || echo "⚠ Migration check skipped"
echo ""

# Check if ChromaDB directory exists and has collections
if [ -d "/app/data/chroma_db" ] && [ "$(ls -A /app/data/chroma_db 2>/dev/null)" ]; then
    echo "✓ Embeddings database found at /app/data/chroma_db"
else
    echo "⚠ No embeddings database found. Building embeddings..."

    # Check if regional documents exist
    if [ -d "/app/Data/regional" ] && [ "$(find /app/Data/regional -type f \( -name "*.pdf" -o -name "*.txt" -o -name "*.docx" -o -name "*.md" \) | head -1)" ]; then
        echo "✓ Regional documents found."

        # Determine which embedding method to use
        if [ "${USE_LOCAL_EMBEDDINGS}" = "true" ]; then
            echo "✓ Using local embeddings (sentence-transformers)"
        elif [ -n "${GOOGLE_API_KEY}" ]; then
            echo "✓ Using Google Gemini embeddings"
        else
            echo "⚠ No GOOGLE_API_KEY found, falling back to local embeddings"
            export USE_LOCAL_EMBEDDINGS=true
            export LOCAL_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
        fi

        echo "⏳ Building regional knowledge base (this may take 1-2 minutes)..."
        python scripts/build_regional_db.py --batch-size 50
        echo "✓ Embeddings created successfully"
    else
        echo "⚠ No regional documents found at /app/Data/regional"
        echo "  Embeddings will be created when documents are added"
    fi
fi

echo ""
echo "=== Starting FastAPI Server ==="
exec python -m uvicorn src.api:app --host 0.0.0.0 --port ${API_PORT:-8000}
