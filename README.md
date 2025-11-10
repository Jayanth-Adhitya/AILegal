# AI Legal Assistant

An automated contract review and analysis system powered by Google Gemini 2.5 Flash, ChromaDB, and LangChain. This system acts as a "digital twin" of a legal associate, automatically reviewing contracts against company policies and generating tracked-changes documents.

## Features

- **Automated Contract Review**: Upload contracts and get AI-powered analysis against company policies
- **Policy-Based Analysis**: Uses RAG (Retrieval Augmented Generation) to match clauses with relevant policies
- **Track Changes Generation**: Outputs Word documents with track changes and comments
- **Clause Classification**: Automatically identifies clause types (liability, IP, payment terms, etc.)
- **Risk Assessment**: Provides risk levels and compliance status for each clause
- **REST API**: Easy-to-use API for integration with existing systems

## Architecture

```
┌─────────────────┐
│  Contract DOCX  │
└────────┬────────┘
         │
         v
┌─────────────────────┐
│  Document Parser    │
│  (python-docx)      │
└────────┬────────────┘
         │
         v
┌─────────────────────┐
│  Clause Extractor   │
│  & Classifier       │
└────────┬────────────┘
         │
         v
┌─────────────────────────────────────────┐
│  Contract Analyzer (Gemini 2.5 Flash)   │
│  - Retrieves relevant policies (RAG)    │
│  - Analyzes compliance                  │
│  - Generates redlines                   │
└────────┬────────────────────────────────┘
         │
         v
┌─────────────────────┐         ┌──────────────────┐
│  DOCX Generator     │         │  ChromaDB        │
│  (Track Changes)    │         │  (Policies/Laws) │
└─────────────────────┘         └──────────────────┘
```

## Prerequisites

- Python 3.9 or higher
- Google Gemini API key
- ~500MB disk space for dependencies

## Installation

### 1. Clone or Download

```bash
cd "Legal Agent"
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the project root:

```bash
# Copy example config
cp .env.example .env

# Edit with your API key
# GOOGLE_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

### 5. Prepare Policy Documents

Create policy files in the `data/policies/` directory:

**Supported Formats**: `.txt`, `.md`, `.pdf`

**Naming Convention**: `PolicyType_Section_Version.{txt|md|pdf}`

Examples:
- `Legal_Liability_v1.0.txt`
- `Commercial_PaymentTerms_v2.1.pdf`
- `Legal_IP_v1.0.md`

Government regulations go in `data/laws/`:
- `GDPR_DataProtection_v1.0.pdf`
- `SOX_Compliance_v1.0.txt`

### 6. Ingest Policies into Vector Store

```bash
python -m src.scripts.ingest_policies
```

Or use the API:

```bash
curl -X POST http://localhost:8000/api/policies/ingest
```

## Usage

### Starting the API Server

```bash
# Start the FastAPI server
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Using the API

#### 1. Upload a Contract

```bash
curl -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@path/to/contract.docx"
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "uploaded",
  "message": "Contract uploaded successfully"
}
```

#### 2. Start Analysis

```bash
curl -X POST http://localhost:8000/api/contracts/{job_id}/analyze
```

#### 3. Check Status

```bash
curl http://localhost:8000/api/contracts/{job_id}/status
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "results": {
    "summary": {
      "contract_type": "Service Agreement",
      "total_clauses_reviewed": 15,
      "compliant_clauses": 12,
      "non_compliant_clauses": 3,
      "overall_risk_assessment": "medium"
    },
    "statistics": {
      "total_clauses": 15,
      "compliant": 12,
      "non_compliant": 3
    }
  }
}
```

#### 4. Download Reviewed Document

```bash
curl -o reviewed_contract.docx \
  http://localhost:8000/api/contracts/{job_id}/download
```

### Analyzing a Single Clause (Quick Test)

```bash
curl -X POST http://localhost:8000/api/analyze/clause \
  -H "Content-Type: application/json" \
  -d '{
    "clause_text": "The Company shall not be liable for any indirect, incidental, or consequential damages.",
    "clause_type": "liability"
  }'
```

### Python SDK Usage

```python
from src.agents.contract_analyzer import ContractAnalyzer

# Initialize analyzer
analyzer = ContractAnalyzer()

# Analyze a contract
results = analyzer.analyze_contract(
    contract_path="path/to/contract.docx",
    output_path="path/to/reviewed_contract.docx"
)

# Print summary
print(f"Contract Type: {results['summary']['contract_type']}")
print(f"Risk Level: {results['summary']['overall_risk_assessment']}")
print(f"Compliant Clauses: {results['statistics']['compliant']}")
print(f"Non-Compliant: {results['statistics']['non_compliant']}")
```

## Project Structure

```
legal-agent/
├── src/
│   ├── core/
│   │   ├── config.py              # Configuration settings
│   │   └── prompts.py             # LLM prompts
│   ├── vector_store/
│   │   ├── embeddings.py          # Policy ingestion
│   │   └── retriever.py           # Semantic search
│   ├── document_processing/
│   │   ├── docx_parser.py         # Parse Word documents
│   │   ├── clause_extractor.py    # Extract & classify clauses
│   │   └── docx_generator.py      # Generate track changes
│   ├── agents/
│   │   ├── policy_checker.py      # RAG policy retrieval
│   │   └── contract_analyzer.py   # Main analysis agent
│   └── api.py                     # FastAPI application
├── data/
│   ├── policies/                  # Company policies
│   ├── laws/                      # Government regulations
│   ├── uploads/                   # Uploaded contracts
│   ├── outputs/                   # Reviewed documents
│   └── chroma_db/                 # Vector store
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

Edit `.env` to customize settings:

```bash
# Model Configuration
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=models/gemini-embedding-001

# Analysis Settings
TEMPERATURE=0.1                    # Low for consistency
CHUNK_SIZE=1000                    # Policy chunk size
RETRIEVAL_K=3                      # Number of policies to retrieve

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
MAX_FILE_SIZE_MB=50
```

## Sample Policy Format

**File**: `data/policies/Legal_Liability_v1.0.txt`

```
Limitation of Liability Policy

Our company limits liability as follows:

1. Maximum Liability Cap
   - Total liability shall not exceed the contract value
   - Cap applies to all claims in aggregate

2. Excluded Damages
   - No liability for indirect or consequential damages
   - Exceptions: gross negligence, willful misconduct, IP infringement

3. Required Terms
   - All contracts must include liability cap
   - Cap must be clearly stated in monetary terms
   - Exceptions must be explicitly listed
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/api/contracts/upload` | POST | Upload contract |
| `/api/contracts/{id}/analyze` | POST | Start analysis |
| `/api/contracts/{id}/status` | GET | Check status |
| `/api/contracts/{id}/download` | GET | Download reviewed doc |
| `/api/analyze/clause` | POST | Analyze single clause |
| `/api/policies/ingest` | POST | Ingest policies |
| `/api/policies/stats` | GET | Vector store stats |

## Output Format

The reviewed document includes:

1. **Summary Page**: Executive overview with statistics and risk assessment
2. **Track Changes**: Visual redlines showing suggested modifications
3. **Comments**: Detailed explanations for each non-compliant clause
4. **Policy Citations**: References to specific company policies
5. **Risk Indicators**: Color-coded risk levels

### Comment Format

```
REJECTED - Non-compliant clause

Reason: Unlimited liability exposure violates company policy

Policy References:
  - Legal_Liability_v1.0: Section 2.1 - Maximum liability must be capped
  - Legal_Liability_v1.0: Section 2.3 - Cap must equal contract value

Risk Level: HIGH

Suggested Alternative:
"The Company's total liability under this Agreement shall not exceed
the total fees paid by Client in the 12 months preceding the claim."
```

## Troubleshooting

### ChromaDB Issues

```bash
# Clear and reinitialize vector store
python -c "from src.vector_store.embeddings import PolicyEmbeddings; pe = PolicyEmbeddings(); pe.clear_collection()"

# Re-ingest policies
python -m src.scripts.ingest_policies
```

### API Key Errors

```bash
# Verify API key is set
python -c "from src.core.config import settings; print(settings.google_api_key[:10])"
```

### Document Parsing Errors

- Ensure contract is a valid .docx file (not .doc or PDF converted to .docx)
- Check file is not password protected
- Verify file size is under limit

## Performance Tips

1. **Batch Processing**: Upload multiple contracts in parallel
2. **Caching**: Policies are cached in ChromaDB for fast retrieval
3. **Async Processing**: Analysis runs in background, allows concurrent jobs
4. **Model Selection**: Gemini 2.5 Flash offers best speed/cost balance

## Security Considerations

- **Local Deployment**: All data stays on-premise with ChromaDB
- **API Keys**: Never commit `.env` file to version control
- **File Cleanup**: Delete analysis jobs after download
- **Access Control**: Add authentication middleware in production

## Extending the System

### Adding Custom Clause Types

Edit `src/core/prompts.py` and add to `CLAUSE_TYPE_CLASSIFIER_PROMPT`:

```python
- my_custom_type: Description of what this clause type covers
```

### Adding Custom Policies

Simply add `.txt` files to `data/policies/` following naming convention and re-ingest.

### Custom Analysis Logic

Extend `ContractAnalyzer.analyze_single_clause()` in `src/agents/contract_analyzer.py`.

## Limitations

- Only supports .docx format (Word 2007+)
- Maximum file size: 50MB (configurable)
- Track changes are visual annotations, not native Word revisions
- Requires internet connection for Gemini API calls

## Future Enhancements

- [ ] PDF contract support
- [ ] Native Word track changes format
- [ ] Multi-language support
- [ ] Custom approval workflows
- [ ] Integration with DocuSign/Adobe Sign
- [ ] Advanced analytics dashboard
- [ ] Fine-tuned model for legal domain

## License

Proof of Concept - Internal Use Only

## Support

For issues or questions:
- Check API documentation: `http://localhost:8000/docs`
- Review logs in console output
- Check ChromaDB stats: `/api/policies/stats`

---

**Built with**: Google Gemini 2.5 Flash, LangChain, ChromaDB, FastAPI, python-docx
