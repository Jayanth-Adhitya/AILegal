# Quick Start Guide - AI Legal Assistant

Get up and running in 5 minutes!

## Step 1: Install Dependencies (2 minutes)

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Configure API Key (1 minute)

```bash
# Copy example config
copy .env.example .env

# Edit .env and add your Gemini API key
# GOOGLE_API_KEY=your_key_here
```

**Get your free Gemini API key**: https://aistudio.google.com/app/apikey

## Step 3: Ingest Sample Policies (1 minute)

We've included two sample policies to get you started:
- `data/policies/Legal_Liability_v1.0.txt`
- `data/policies/Commercial_PaymentTerms_v1.0.txt`

Ingest them into the vector store:

```bash
python -m src.scripts.ingest_policies
```

Expected output:
```
✅ Ingestion Complete!
   - Policies ingested: 10 chunks
   - Laws ingested: 0 chunks
```

## Step 4: Test with Sample Clause (1 minute)

```bash
python main.py clause "The Company shall not be liable for any indirect, incidental, or consequential damages exceeding the contract value."
```

You should see:
- Clause classification
- Compliance status
- Risk assessment
- Policy references

## Step 5: Analyze a Contract (Optional)

### Using CLI:

```bash
python main.py analyze path/to/contract.docx
```

### Using API:

```bash
# Terminal 1: Start API server
python -m uvicorn src.api:app --reload

# Terminal 2: Upload and analyze
curl -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@contract.docx"

# Use the job_id from response
curl -X POST http://localhost:8000/api/contracts/{job_id}/analyze

# Check status
curl http://localhost:8000/api/contracts/{job_id}/status

# Download result
curl -o reviewed.docx http://localhost:8000/api/contracts/{job_id}/download
```

## Next Steps

### Add Your Own Policies

Create policy files in `data/policies/` in `.txt`, `.md`, or `.pdf` format:

**Filename**: `PolicyType_Section_Version.{txt|md|pdf}`

Examples:
- `Legal_IP_v1.0.txt`
- `Commercial_Terms_v1.0.pdf`
- `Data_Privacy_v2.0.md`

**Content structure**:
```
Policy Title

Version: 1.0
Department: Legal

SECTION 1: OVERVIEW
[Policy content here]

SECTION 2: REQUIREMENTS
[Specific requirements]

SECTION 3: FORBIDDEN PROVISIONS
[What to reject]

SECTION 4: REQUIRED LANGUAGE
[Acceptable clause examples]
```

Then re-ingest:
```bash
python -m src.scripts.ingest_policies
```

### Customize Settings

Edit `.env` file:

```bash
# Use more retrieval results for better accuracy
RETRIEVAL_K=5

# Adjust chunk size for longer policies
CHUNK_SIZE=1500

# Change temperature (0.0 = most consistent, 1.0 = most creative)
TEMPERATURE=0.1
```

### View API Documentation

```bash
python -m uvicorn src.api:app --reload
```

Visit: http://localhost:8000/docs

## Common Issues

### "Invalid API key"
- Check your `.env` file has `GOOGLE_API_KEY=...`
- Verify key at https://aistudio.google.com/app/apikey

### "No policies found"
- Run `python -m src.scripts.ingest_policies`
- Check files exist in `data/policies/`

### "Module not found"
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`

## Need Help?

- Check full README.md for detailed documentation
- View API docs at http://localhost:8000/docs
- Check logs for detailed error messages

---

**You're all set!** 🚀

The system is now ready to analyze contracts against your company policies.
