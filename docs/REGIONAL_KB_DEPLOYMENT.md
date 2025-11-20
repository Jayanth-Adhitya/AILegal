# Regional Knowledge Base - Deployment Guide

This guide explains how to **pre-build and package** the regional knowledge base for efficient deployment.

## Overview

The regional knowledge base uses ChromaDB, which **persists data to disk**. This means:

✅ **You only need to embed documents once**
✅ **The database can be packaged in your Docker image**
✅ **No need to include source PDFs in deployment**
✅ **Instant startup (no re-ingestion required)**

---

## Deployment Strategy Comparison

### Strategy 1: Dynamic Loading (Current Default)

**How it works:**
```
Docker Start → Check if collections exist → If empty, ingest documents → Use DB
```

**Pros:**
- Easy to update documents (just replace files and restart)
- No build step required

**Cons:**
- Source documents must be in deployment
- First startup takes ~10 seconds per region
- Larger Docker image (includes PDFs)

**Best for:** Development, frequent document updates

---

### Strategy 2: Pre-Built Database (Recommended for Production)

**How it works:**
```
Build Time → Embed all documents → Package DB in image → Deploy → Use immediately
```

**Pros:**
- ⚡ **Instant startup** (<1 second)
- 📦 **Smaller image** (no source PDFs)
- 🔒 **Immutable** (database version-controlled)
- 🚀 **Faster deployments**

**Cons:**
- Requires build step
- Document updates need rebuild

**Best for:** Production, containerized deployments

---

## How to Pre-Build the Database

### Step 1: Prepare Your Documents

Place your Dubai legal documents in the regional directory:

```bash
# Copy your documents
cp /dubai_docs/*.pdf data/regional/dubai_uae/
cp /dubai_docs/*.docx data/regional/dubai_uae/

# Verify
ls -lh data/regional/dubai_uae/
```

Supported formats: `.pdf`, `.docx`, `.txt`, `.md`

---

### Step 2: Build the Database

Run the build script:

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Build all regional databases (default settings: 50 chunks/batch, 1s delay)
python scripts/build_regional_db.py

# OR: Custom rate limiting (if hitting API limits)
python scripts/build_regional_db.py --batch-size 25 --delay 2.0
```

**Expected output:**
```
🔨 Building Regional Knowledge Bases
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️  Rate Limiting Configuration:
   - Batch size: 50 chunks per batch
   - Delay: 1.0s between batches
   - Max RPM: 1500
   - Retry attempts: 5 (with exponential backoff)
   - Estimated time for 300 chunks: ~6.0s

📋 Regions to build: dubai_uae

🌍 Building region: dubai_uae
   Name: Dubai, UAE
   Data directory: data/regional/dubai_uae
   📄 Found 15 documents

[INFO] Embedding 342 texts in 7 batch(es) (batch_size=50, delay=1.0s)
[INFO] Processing batch 1/7 (50 texts)...
[INFO] Waiting 1.0s before next batch...
[INFO] Processing batch 2/7 (50 texts)...
...
[INFO] ✅ Successfully embedded 342 texts

   ✅ Ingested 342 chunks

✅ Build Complete!
   Total chunks ingested: 342
   Database location: ./chroma_db/

📊 Collection Statistics:
   policies_global: 250 documents
   policies_dubai_uae: 342 documents
```

**What happened:**
- All PDFs/DOCX files were parsed
- Text was split into chunks
- Chunks were embedded using Google's embedding model **with automatic rate limiting**
- Vectors saved to `./chroma_db/policies_dubai_uae/`

**⚠️ Important - Rate Limiting:**
- Gemini embedding API has rate limits (1500 RPM for free tier)
- The system automatically handles rate limits with batching and retry logic
- See `docs/RATE_LIMITING.md` for detailed configuration guide
- If you see rate limit warnings, adjust `--batch-size` and `--delay`

---

### Step 3: Test the Database

Verify everything works:

```bash
python scripts/test_regional_retrieval.py
```

**Expected output:**
```
🧪 Testing Regional Knowledge Base Retrieval

📊 Test 1: Checking collection statistics...
   ✅ policies_global: 250 documents
   ✅ policies_dubai_uae: 342 documents

🌍 Test 2: Testing IP-based region detection...
   IP: 5.1.83.46
      ✅ Country: AE (expected: AE)
      ✅ Region: dubai_uae (expected: dubai_uae)

🔍 Test 3: Testing regional document retrieval...
   Query: 'payment terms and liability limitations'
   Mode: Global only
   ✅ Retrieved 5 global documents
   Mode: Dubai + Global
   ✅ Retrieved 5 documents (global + regional)
      - 3 from Dubai KB
      - 2 from Global KB

✅ All tests completed!
```

---

### Step 4: Package in Docker

Update your `Dockerfile` to copy the pre-built database:

```dockerfile
# ============================================
# Option A: Package Pre-Built Database
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY main.py ./

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy GeoIP database
COPY geolite2/GeoLite2-Country.mmdb ./geolite2/

# ✨ COPY PRE-BUILT CHROMADB DATABASE ✨
COPY chroma_db/ ./chroma_db/

# ❌ NO NEED TO COPY SOURCE DOCUMENTS ❌
# (They're already embedded in chroma_db/)

# Set environment variables
ENV REGIONAL_KB_ENABLED=true
ENV CHROMA_DB_PATH=/app/chroma_db

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key changes:**
- ✅ `COPY chroma_db/ ./chroma_db/` - Includes pre-built database
- ❌ Don't copy `data/regional/` - Not needed anymore
- ⚡ Instant startup - No ingestion on first run

---

### Step 5: Build and Deploy

```bash
# Build Docker image
docker build -t legal-agent:latest .

# Run container
docker run -p 8000:8000 legal-agent:latest

# Check logs (should show instant startup)
docker logs <container_id>
```

**Expected logs:**
```
[INFO] Starting application...
[INFO] Initializing ChromaDB client at /app/chroma_db
[INFO] ✅ Regional KB startup check (0.2s):
       - policies_global: 250 docs (already ingested)
       - policies_dubai_uae: 342 docs (already ingested)
[INFO] Application ready in 1.3s 🚀
```

---

## Updating Documents

When you need to add/update Dubai documents:

### Development (Strategy 1)
```bash
# Add new documents
cp new_contract.pdf data/regional/dubai_uae/

# Delete old database
rm -rf chroma_db/

# Restart application (will re-ingest)
python main.py
```

### Production (Strategy 2)
```bash
# Add new documents
cp new_contract.pdf data/regional/dubai_uae/

# Rebuild database
rm -rf chroma_db/
python scripts/build_regional_db.py

# Rebuild Docker image
docker build -t legal-agent:v2 .

# Deploy new version
docker push legal-agent:v2
```

---

## Environment Variables

Configure regional KB behavior:

```bash
# Enable/disable regional KB
REGIONAL_KB_ENABLED=true

# Global policy weight (prefer company policies)
REGIONAL_GLOBAL_WEIGHT=1.1

# ChromaDB persistence location
CHROMA_DB_PATH=./chroma_db

# GeoIP database location
GEOIP_DB_PATH=./geolite2/GeoLite2-Country.mmdb

# Embedding API Rate Limiting (Gemini)
EMBEDDING_BATCH_SIZE=50               # Chunks per batch
EMBEDDING_DELAY_SECONDS=1.0           # Delay between batches
EMBEDDING_REQUESTS_PER_MINUTE=1500    # Your API tier limit (free: 1500)
```

**Rate Limiting Tips:**
- **Free tier:** Keep defaults (50 chunks/batch, 1s delay)
- **Hitting limits:** Reduce to 25 chunks/batch, 2s delay
- **Paid tier:** Increase to 100 chunks/batch, 0.5s delay
- See `docs/RATE_LIMITING.md` for detailed guide

---

## Disk Space Usage

Estimate disk space for ChromaDB:

| Collection | Documents | Chunks | Size (approx) |
|-----------|-----------|--------|---------------|
| Global KB | 50 PDFs   | 250    | ~15 MB        |
| Dubai KB  | 15 PDFs   | 342    | ~20 MB        |
| **Total** |           |        | **~35 MB**    |

**Rule of thumb:** ~50-100 KB per embedded chunk

---

## Troubleshooting

### Database Not Found on Startup

**Symptom:** Logs show "Ingesting regional KB..." on every startup

**Cause:** ChromaDB path not properly mounted or copied

**Fix:**
```bash
# Check if database exists in container
docker exec <container_id> ls -lh /app/chroma_db/

# Verify COPY command in Dockerfile
COPY chroma_db/ ./chroma_db/
```

---

### Empty Regional Results

**Symptom:** Regional retrieval returns no documents

**Cause:** Database not built, or collection empty

**Fix:**
```bash
# Check collection stats
python scripts/test_regional_retrieval.py

# Rebuild if needed
rm -rf chroma_db/
python scripts/build_regional_db.py
```

---

### Slow Startup Despite Pre-Built DB

**Symptom:** First startup still takes ~10 seconds

**Cause:** Application still running ingestion check

**Optimization:** The current implementation always checks collections on startup (safe but adds ~0.5s). This is acceptable for most use cases. If you need true zero-check startup, you can disable the startup ingestion in `src/api.py`:

```python
@app.on_event("startup")
async def startup_event():
    # ... existing code ...

    # Comment out this section if DB is pre-built
    # if config_settings.regional_kb_enabled:
    #     logger.info("Checking regional knowledge bases...")
    #     embeddings = PolicyEmbeddings()
    #     for region_code in get_enabled_regions():
    #         embeddings.ingest_regional_directory(...)
```

**Trade-off:** Faster startup, but won't auto-ingest if database is missing

---

## Best Practices

### Development
- ✅ Use Strategy 1 (dynamic loading)
- ✅ Keep source documents in version control
- ✅ Use `.env` for configuration
- ✅ Run `test_regional_retrieval.py` after changes

### Production
- ✅ Use Strategy 2 (pre-built database)
- ✅ Build database during CI/CD pipeline
- ✅ Version-tag Docker images with database versions
- ✅ Monitor collection sizes via `/api/debug/regional-kb-info`
- ✅ Keep GeoIP database updated monthly

---

## CI/CD Integration Example

**GitHub Actions / GitLab CI:**

```yaml
name: Build Regional KB

jobs:
  build:
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Download GeoIP database
        run: |
          mkdir -p geolite2
          curl -L https://github.com/P3TERX/GeoLite.mmdb/releases/latest/download/GeoLite2-Country.mmdb \
            -o geolite2/GeoLite2-Country.mmdb

      - name: Build regional knowledge bases
        run: |
          pip install -r requirements.txt
          python scripts/build_regional_db.py

      - name: Test regional retrieval
        run: python scripts/test_regional_retrieval.py

      - name: Build Docker image
        run: docker build -t legal-agent:${{ github.sha }} .

      - name: Push to registry
        run: docker push legal-agent:${{ github.sha }}
```

---

## Summary

**For production deployments:**

1. 📄 **Add documents** to `data/regional/dubai_uae/`
2. 🔨 **Build database** with `python scripts/build_regional_db.py`
3. 🧪 **Test** with `python scripts/test_regional_retrieval.py`
4. 📦 **Package** in Docker with `COPY chroma_db/ ./chroma_db/`
5. 🚀 **Deploy** with instant startup and no source documents

**Result:** ⚡ Fast, efficient, production-ready regional knowledge base!
