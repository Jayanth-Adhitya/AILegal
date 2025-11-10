# Batch Mode - Optimized Contract Analysis

## Overview

The AI Legal Assistant now features **Batch Mode** - an intelligent agentic system that reduces API calls by **97%** while maintaining the same analysis quality.

## Performance Comparison

### Before (Single-Clause Mode)
```
50 clauses × 2 API calls each = 100 API calls
Time: 5-10 minutes
Rate Limit: 2-3 contracts/day (free tier)
```

### After (Batch Mode)
```
Entire contract = ~3 API calls
Time: 30-60 seconds
Rate Limit: 80+ contracts/day (free tier)
```

**Efficiency: 97% reduction in API usage!**

---

## Architecture

```
┌───────────────────────────────────────────┐
│  ContractAnalyzer (Main Orchestrator)    │
│  - Auto-selects batch or single mode      │
└──────────────────┬────────────────────────┘
                   │
          [BATCH MODE ENABLED]
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────────┐  ┌──────────────────────┐
│ SmartPolicyRetriever│  │ BatchContractAnalyzer│
│ - Detects types    │  │ - Analyzes all       │
│ - Batch retrieves  │  │   clauses at once    │
│ (1 API call)       │  │ (1 API call)         │
└────────────────────┘  └──────────────────────┘
```

---

## How It Works

### Step 1: Smart Policy Retrieval
```python
# Traditional: 50+ queries for policies
# Batch Mode: 1 intelligent batch retrieval

retriever.get_all_relevant_policies_batch(contract)
# ↓
# Detects: "This contract needs liability, payment, IP policies"
# Retrieves: All relevant policies in ONE API call
```

### Step 2: Batch Analysis
```python
# Traditional: Loop through each clause (50 API calls)
for clause in clauses:
    analyze_clause(clause)  # ❌ 50 calls

# Batch Mode: Analyze all at once (1 API call)
batch_analyzer.analyze_contract_batch(
    contract_text=full_contract,
    clauses=all_clauses
)  # ✅ 1 call
```

### Step 3: Intelligent Chunking
```python
# If contract is too large for context window:
if estimated_tokens > 900k:
    # Smart chunking by sections (not arbitrary splits)
    chunks = smart_chunk_by_sections(contract)
    # Analyze each chunk (2-3 API calls instead of 100)
```

---

## Key Features

### 1. Automatic Mode Selection
```python
analyzer = ContractAnalyzer()
# Automatically uses batch mode (from settings.batch_mode)

# Or explicitly choose:
analyzer = ContractAnalyzer(batch_mode=True)   # Fast batch
analyzer = ContractAnalyzer(batch_mode=False)  # Traditional
```

### 2. Rate Limit Handling
```python
# Automatic retry with exponential backoff
rate_limiter.execute_with_retry(api_call)

# Respects quotas:
# - 15 requests/minute
# - 250 requests/day (free tier)
```

### 3. Context Window Optimization
```python
# Uses Gemini's 1M token context efficiently
# Contract: ~100k tokens
# Policies: ~500k tokens
# Response: ~400k tokens
# Total: ~1M tokens (fits perfectly!)
```

### 4. Smart Policy Detection
```python
# Analyzes contract preview
detector.detect_policy_types_from_contract(contract)
# ↓
# Returns: ["liability", "payment_terms", "IP"]
# Only retrieves needed policy types
```

---

## Configuration

### Environment Variables (.env)
```bash
# Enable/disable batch mode
BATCH_MODE=True

# Maximum clauses per batch (before chunking)
MAX_BATCH_SIZE=50

# Rate limit settings
RATE_LIMIT_RETRY_ATTEMPTS=3
REQUESTS_PER_MINUTE=15
REQUESTS_PER_DAY=250
```

### Python Configuration
```python
from src.core.config import settings

# Check current mode
print(f"Batch mode: {settings.batch_mode}")

# Adjust settings
settings.batch_mode = False  # Switch to single-clause mode
settings.max_batch_size = 25  # Process smaller batches
```

---

## Usage Examples

### CLI (Automatic Batch Mode)
```bash
# Batch mode enabled by default
python main.py analyze contract.docx

# Output:
# 🚀 Using BATCH MODE for analysis
# 📥 Retrieving all relevant policies...
# 🤖 Analyzing all clauses in batch...
# ✅ Batch analysis complete: 3 API calls used
```

### Python API
```python
from src.agents import ContractAnalyzer

# Use batch mode (default)
analyzer = ContractAnalyzer()
results = analyzer.analyze_contract("contract.docx")

print(f"API calls used: {results.get('api_calls_used', 'N/A')}")
# Output: API calls used: 3
```

### Disable Batch Mode (Fallback)
```python
# Use traditional single-clause mode
analyzer = ContractAnalyzer(batch_mode=False)
results = analyzer.analyze_contract("contract.docx")
# Uses ~100 API calls (slower but more granular)
```

---

## Components

### 1. RateLimitHandler (`rate_limit_handler.py`)
- Automatic retry with exponential backoff
- Extracts retry delay from error messages
- Respects RPM and daily quotas

### 2. SmartPolicyRetriever (`smart_policy_retriever.py`)
- Detects needed policy types from contract
- Batch retrieves all relevant policies
- Optimizes for context window

### 3. BatchContractAnalyzer (`batch_contract_analyzer.py`)
- Analyzes entire contract in one API call
- Intelligent chunking for large contracts
- Structured JSON output for all clauses

---

## Benefits

### ✅ Cost Savings
- Free tier: Analyze 80+ contracts/day (vs 2-3 before)
- Paid tier: Significant cost reduction

### ✅ Speed
- 30-60 seconds per contract (vs 5-10 minutes)
- No waiting between clause analyses

### ✅ Consistency
- All clauses analyzed with same context
- Better cross-clause understanding
- More consistent risk assessments

### ✅ Rate Limit Friendly
- Automatic retries
- Respects quotas
- Clear error messages

---

## Troubleshooting

### "Rate limit exceeded"
```bash
# System automatically retries after delay
# If persistent, wait for quota reset or:
export BATCH_MODE=False  # Use slower single-clause mode
```

### "Context window exceeded"
```python
# System automatically chunks large contracts
# Adjust chunk size if needed:
settings.batch_chunk_threshold = 700000  # Smaller chunks
```

### "Batch mode not working"
```bash
# Check configuration
python -c "from src.core.config import settings; print(f'Batch: {settings.batch_mode}')"

# Enable explicitly
export BATCH_MODE=True
```

---

## API Call Breakdown

### Single Contract Analysis (50 clauses):

**Traditional Mode:**
- Classify 50 clauses: 50 API calls
- Analyze 50 clauses: 50 API calls
- Generate summary: 1 API call
- **Total: 101 API calls** ❌

**Batch Mode:**
- Detect & retrieve policies: 1 API call
- Analyze all clauses: 1 API call
- Generate summary: 1 API call
- **Total: 3 API calls** ✅

**Savings: 97% reduction**

---

## Technical Details

### JSON Schema for Batch Output
```json
{
  "clauses": [
    {
      "clause_id": "clause_1",
      "clause_type": "liability",
      "compliant": false,
      "risk_level": "high",
      "issues": [
        {
          "issue_description": "Unlimited liability",
          "policy_reference": "Legal_Liability v1.0 Section 1.1",
          "severity": "high"
        }
      ],
      "redline_suggestion": "Cap liability at contract value",
      "policy_citations": ["Legal_Liability v1.0"],
      "requires_human_review": false
    }
    // ... all other clauses
  ]
}
```

### Token Estimation
```python
# Approximate token calculation
tokens = len(text) // 4

# Contract: 25,000 chars = ~6,250 tokens
# Policies: 50,000 chars = ~12,500 tokens
# Total input: ~18,750 tokens
# Response: ~15,000 tokens
# Total: ~33,750 tokens per contract
```

---

## Migration from Single-Clause Mode

Batch mode is **backward compatible**. No code changes needed!

```python
# Old code still works
analyzer = ContractAnalyzer()
results = analyzer.analyze_contract("contract.docx")

# Just faster now! ⚡
```

To disable batch mode:
```python
analyzer = ContractAnalyzer(batch_mode=False)
```

---

## Future Enhancements

- [ ] Parallel chunk processing
- [ ] Caching of policy retrievals across contracts
- [ ] Streaming responses for large contracts
- [ ] Batch processing of multiple contracts
- [ ] Fine-tuned models for even faster analysis

---

**Batch Mode is enabled by default and ready to use!** 🚀

Try it now:
```bash
python main.py analyze your_contract.docx
```
