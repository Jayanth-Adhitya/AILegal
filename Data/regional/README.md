# Regional Knowledge Bases

This directory contains region-specific legal documents and sample agreement templates for the Legal Agent system.

## Directory Structure

```
regional/
├── README.md (this file)
└── {region_code}/          # One directory per region
    ├── document1.pdf
    ├── document2.txt
    ├── document3.md
    └── ...
```

## Supported Regions

### Dubai, UAE (`dubai_uae/`)
**Status**: Active
**Country Codes**: AE (United Arab Emirates)
**Legal Jurisdiction**: UAE Federal Law + DIFC
**Document Types**: UAE-specific legal documents, DIFC regulations, sample agreements

## Adding Regional Documents

### Step 1: Prepare Documents
Place your regional legal documents in the appropriate region directory:
- **Supported formats**: PDF, TXT, MD
- **File naming**: Use descriptive names (e.g., `UAE_Contract_Law_v1.pdf`, `DIFC_Commercial_Companies_Law.pdf`)
- **Content**: Legal statutes, regulations, sample agreement templates, legal guidance

### Step 2: Organize by Region
```bash
# For Dubai/UAE documents:
cp your_documents.pdf data/regional/dubai_uae/

# For future regions (e.g., Singapore):
mkdir -p data/regional/singapore
cp your_documents.pdf data/regional/singapore/
```

### Step 3: Configure Region (if new region)
Edit `src/core/config.py` and add region configuration:

```python
REGION_CONFIG = {
    "your_region_code": {
        "collection_name": "policies_your_region_code",
        "data_directory": "data/regional/your_region_code",
        "countries": ["XX"],  # ISO country code(s)
        "enabled": True,
        "metadata": {
            "region_name": "Your Region Name",
            "legal_jurisdiction": "Your Legal System",
            "language": "en"
        }
    }
}
```

### Step 4: Restart Application
Regional documents are ingested automatically on application startup. After adding new documents:

```bash
# Restart the application to ingest new regional documents
docker-compose restart backend
# OR
python main.py
```

## Document Ingestion Process

1. **Startup**: Application reads `REGION_CONFIG` from `src/core/config.py`
2. **Discovery**: For each enabled region, scans `data/regional/{region_code}/` directory
3. **Extraction**: Extracts text from PDF, TXT, and MD files
4. **Chunking**: Splits documents into chunks (~1000 chars with 200 char overlap)
5. **Embedding**: Generates embeddings using Google Gemini embedding model
6. **Storage**: Stores in ChromaDB collection `policies_{region_code}`
7. **Metadata**: Tags each chunk with region, jurisdiction, source type

## Idempotency

The system checks if a regional collection is already populated before ingesting:
- **First run**: Ingests all documents (takes 5-15 seconds depending on document count)
- **Subsequent runs**: Skips ingestion if collection already has documents (fast startup)

To force re-ingestion, delete the ChromaDB collection:
```bash
# From within Docker container or Python environment:
from src.vector_store.embeddings import PolicyEmbeddings
p = PolicyEmbeddings()
p.chroma_client.delete_collection("policies_dubai_uae")  # Replace with your region
```

## How Regional Retrieval Works

When a user accesses the system:

1. **Region Detection**: User's IP address is mapped to country code using GeoIP database
2. **Region Mapping**: Country code is mapped to region code (e.g., "AE" → "dubai_uae")
3. **Policy Retrieval**: System queries:
   - Global company policies collection (always)
   - Regional legal documents collection (if region detected)
4. **Merging**: Results from both collections are merged by relevance score
5. **LLM Context**: Combined policies provided to LLM for legal analysis

**Example**: A user from Dubai asking about payment terms receives:
- Company payment policy (global)
- UAE Commercial Transactions Law (regional)
- DIFC payment regulations (regional)

## File Format Guidelines

### PDF Files
- **Best for**: Official legal statutes, regulations, published guides
- **Requirements**: Text-based PDFs (not scanned images)
- **Extraction**: Automatic text extraction via PyPDF2

### TXT Files
- **Best for**: Plain text legal documents, transcribed statutes
- **Requirements**: UTF-8 encoding
- **Format**: Plain text with clear section headings

### Markdown Files (.md)
- **Best for**: Structured legal documents, sample agreements
- **Requirements**: Standard Markdown syntax
- **Benefits**: Preserves formatting and structure

## Document Quality Tips

1. **Clear Structure**: Use headings, sections, and clear paragraph breaks
2. **Accurate Content**: Ensure legal accuracy and up-to-date information
3. **Source Attribution**: Include document source, date, and version in filename
4. **Chunk-Friendly**: Break long documents into logical sections
5. **Avoid Duplicates**: Don't include same content in multiple files

## Troubleshooting

### Issue: Documents not appearing in policy chat
**Check**:
- Documents placed in correct directory (`data/regional/{region_code}/`)
- Region is enabled in `config.py` (`"enabled": True`)
- Application has been restarted after adding documents
- Logs show ingestion success: `grep "Ingested.*chunks for region" logs/app.log`

### Issue: Wrong regional content for users
**Check**:
- GeoIP database is present: `ls geolite2/GeoLite2-Country.mmdb`
- IP address detection working: Check debug logs for region detection
- Country code mapping is correct in `REGION_CONFIG`

### Issue: Slow startup after adding regional documents
**Expected**: First-time ingestion takes 5-15 seconds for 50-100 documents
**If slower**: Check document sizes (very large PDFs take longer to process)

## Storage Locations

- **Documents**: `data/regional/{region_code}/` (source files)
- **Embeddings**: `data/chroma_db/` (ChromaDB vector store)
- **Logs**: Application logs show ingestion details

## Security Considerations

- **Access Control**: Regional documents are visible to all users from that region (not company-specific)
- **Sensitive Data**: Do not include confidential company information in regional documents
- **Legal Compliance**: Ensure you have rights to use and distribute regional legal documents

## Future Enhancements

- **Runtime Updates**: Upload regional documents via API (currently requires restart)
- **Per-Company Regions**: Custom regional content per company
- **Manual Region Selection**: Allow users to override IP-based detection
- **Multiple Regions**: Support users needing documents from multiple jurisdictions

---

**Last Updated**: 2025-11-20
**Contact**: See project README for support information
