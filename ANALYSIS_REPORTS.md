# Analysis Reports - Transparent Contract Review

## Overview

The AI Legal Assistant now generates **3 comprehensive reports** for every contract analysis, providing complete transparency into what was checked and what needs to change.

---

## Generated Reports

### 1. 📝 Reviewed Contract (Track Changes)
**File**: `contract_reviewed.docx`

The original contract with AI-generated comments and track changes markup.

**Features:**
- Visual redlines showing suggested changes
- Comments explaining why clauses are non-compliant
- Policy citations for each issue
- Ready for human review in Microsoft Word

**Use Case**: Send to legal team or vendor with AI recommendations

---

### 2. 📊 Detailed Analysis Report
**File**: `contract_DETAILED_REPORT.docx`

A comprehensive Word document showing every single clause analyzed.

**Contents:**

#### Title Page
- Contract name and metadata
- Generation timestamp
- Powered by Gemini 2.5 Flash

#### Executive Summary
- Contract type identification
- Overall risk assessment (color-coded)
- Compliance statistics
- Key findings summary

#### Statistics Dashboard
- Total clauses reviewed
- Compliance percentage
- Clause type distribution
- Risk level breakdown

#### Clause-by-Clause Analysis
For **each clause**, shows:
- ✅/❌ Compliance status
- Original text (quoted)
- Clause type classification
- Risk level (color-coded: LOW, MEDIUM, HIGH, CRITICAL)
- **Specific issues found** with policy references
- **Why it's non-compliant** (detailed explanation)
- **Recommended alternative wording** (if non-compliant)
- Policy citations
- Review notes for edge cases

#### Risk Assessment Matrix
- Clauses grouped by risk level
- Critical issues highlighted
- Quick reference for prioritization

#### Recommendations & Next Steps
- Overall contract assessment
- Immediate actions required
- SME review requirements
- Implementation guidance

**Use Case**: Complete documentation for audit trail and decision-making

---

### 3. 🌐 Interactive HTML Summary
**File**: `contract_SUMMARY.html`

A beautiful, interactive web page for quick review.

**Features:**

#### Statistics Cards
- Total clauses
- Compliant count
- Non-compliant count
- Compliance rate percentage

#### Filter Buttons
- **All Clauses** - See everything
- **Non-Compliant Only** - Focus on issues
- **Critical Risk** - Urgent items only

#### Each Clause Card Shows:
- Status badge (✅ Compliant / ❌ Non-Compliant)
- Risk level badge (color-coded)
- Original clause text
- Issues identified (expandable)
- Recommended alternative (if applicable)
- Policy reference tags

**Use Case**: Quick review in browser, share via link, presentation-ready

---

## Example Output

When you analyze a contract, you get:

```
💾 Generated Files:

   📝 Reviewed Contract (with track changes):
      C:\...\Distribution_Agreement_reviewed.docx

   📊 Detailed Analysis Report (Word document):
      C:\...\Distribution_Agreement_DETAILED_REPORT.docx
      → Open this to see all clauses checked and changes recommended

   🌐 Interactive HTML Summary (open in browser):
      C:\...\Distribution_Agreement_SUMMARY.html
      → Filterable view of all analysis results
```

---

## Usage

### Automatic Generation

Reports are **automatically generated** when you analyze a contract:

```bash
python main.py analyze contract.docx
```

No extra flags needed! All 3 reports are created by default.

### API Usage

```python
from src.agents import ContractAnalyzer

analyzer = ContractAnalyzer()
results = analyzer.analyze_contract(
    contract_path="contract.docx",
    output_path="reviewed_contract.docx"
)

# Access report paths
output_files = results["output_files"]
print(f"Detailed report: {output_files['detailed_report']}")
print(f"HTML summary: {output_files['html_summary']}")
```

---

## Report Details

### Detailed Report Structure

```
📄 Distribution_Agreement_DETAILED_REPORT.docx
│
├── Title Page
│   └── Contract info, timestamp, AI branding
│
├── Executive Summary
│   ├── Contract type
│   ├── Risk assessment (🟢🟡🔴)
│   ├── Statistics
│   └── Key findings
│
├── Statistics Dashboard
│   ├── Compliance metrics
│   ├── Clause type breakdown
│   └── Risk distribution
│
├── Clause-by-Clause Analysis (50+ clauses)
│   │
│   ├── ❌ Clause 1: Liability
│   │   ├── Original Text: "Company shall not be liable..."
│   │   ├── Status: NON-COMPLIANT
│   │   ├── Risk: HIGH
│   │   ├── Issues:
│   │   │   • Unlimited liability exposure
│   │   │   • Policy: Legal_Liability v1.0 Section 1.1
│   │   ├── Why Non-Compliant:
│   │   │   "Violates company policy requiring..."
│   │   ├── Recommended Alternative:
│   │   │   "Company's liability shall not exceed..."
│   │   └── Policy References:
│   │       • Legal_Liability_v1.0
│   │
│   ├── ✅ Clause 2: Confidentiality
│   │   ├── Original Text: "Parties agree to maintain..."
│   │   ├── Status: COMPLIANT
│   │   ├── Risk: LOW
│   │   └── Policy References:
│   │       • Legal_Confidentiality_v1.0
│   │
│   └── ... (continues for all clauses)
│
├── Risk Assessment Matrix
│   ├── CRITICAL RISK CLAUSES (2)
│   ├── HIGH RISK CLAUSES (5)
│   ├── MEDIUM RISK CLAUSES (8)
│   └── LOW RISK CLAUSES (35)
│
└── Recommendations & Next Steps
    ├── Overall Assessment
    ├── Immediate Actions (numbered)
    └── SME Review Requirements
```

---

## HTML Summary Features

### Interactive Filtering

```html
🔘 All Clauses    🔴 Non-Compliant Only    🚨 Critical Risk
```

Click to filter view instantly.

### Visual Design

- **Green cards** = Compliant ✅
- **Red cards** = Non-Compliant ❌
- **Color-coded badges** = Risk levels
- **Expandable sections** = Details on demand

### Responsive Layout

- Works on desktop and mobile
- Print-friendly
- Dark mode support (coming soon)

---

## Sample Clause Detail

### In Detailed Report (Word):

```
❌ Clause 15: Limitation of Liability

Original Text:
"The Company shall not be liable for any indirect, incidental, or
consequential damages arising from this Agreement, regardless of
the form of action."

Compliance Status: NON-COMPLIANT ✗
Risk Level: HIGH

Issues Identified:
• Unlimited liability exposure for direct damages
  Policy: Legal_Liability_v1.0 Section 1.1
  Severity: HIGH

• Missing liability cap requirement
  Policy: Legal_Liability_v1.0 Section 1.2
  Severity: HIGH

Why This is Non-Compliant:
Company policy requires ALL contracts to include a maximum liability
cap equal to the contract value. This clause only excludes indirect
damages but does not cap direct damages, creating unlimited liability
exposure.

Recommended Alternative:
"The Company's total aggregate liability under this Agreement shall not
exceed the total fees paid by Client in the twelve (12) months preceding
the claim. The Company shall not be liable for any indirect, incidental,
special, or consequential damages."

Policy References:
• Legal_Liability_v1.0 - Section 1.1 (Required Cap)
• Legal_Liability_v1.0 - Section 2.1 (Indirect Damages Exclusion)

─────────────────────────────────────────────────────────────
```

### In HTML Summary:

```html
┌────────────────────────────────────────────┐
│ Clause 15: Limitation of Liability        │
│ ❌ NON-COMPLIANT    🔴 HIGH RISK          │
├────────────────────────────────────────────┤
│ Original Text:                             │
│ "The Company shall not be liable..."      │
│                                            │
│ ⚠️ Issues Identified:                     │
│ • Unlimited liability exposure             │
│   Policy: Legal_Liability_v1.0 Sec 1.1    │
│                                            │
│ 💡 Recommended Alternative:               │
│ "The Company's total aggregate liability   │
│  shall not exceed..."                      │
│                                            │
│ 📚 Policy References:                     │
│ [Legal_Liability_v1.0] [Section 1.1]     │
└────────────────────────────────────────────┘
```

---

## Benefits

### ✅ Complete Transparency
Every clause is documented with AI reasoning

### ✅ Audit Trail
Detailed reports serve as compliance documentation

### ✅ Multiple Formats
- Word for lawyers (track changes)
- Word for management (detailed analysis)
- HTML for quick review (interactive)

### ✅ Easy Sharing
- Email Word documents
- Host HTML on internal portal
- Print for meetings

### ✅ Decision Support
Clear risk levels and recommendations guide next steps

---

## Customization

### Disable Report Generation

If you only want the tracked changes document:

```python
# Edit src/agents/contract_analyzer.py
# Comment out report generation section
```

### Custom Report Styling

Edit `src/document_processing/analysis_report_generator.py`:

```python
# Customize colors
risk_colors = {
    "LOW": RGBColor(0, 128, 0),
    "MEDIUM": RGBColor(255, 165, 0),
    # ... change to your brand colors
}

# Customize HTML template
html = """
<style>
    /* Add your CSS here */
</style>
"""
```

---

## File Naming Convention

```
Original:      Distribution_Agreement.docx

Generated:
├── Distribution_Agreement_reviewed.docx
├── Distribution_Agreement_DETAILED_REPORT.docx
└── Distribution_Agreement_SUMMARY.html
```

All files saved in the same directory as output_path.

---

## Performance

Report generation adds **~2-5 seconds** to analysis time:
- Detailed report: ~3 seconds
- HTML summary: ~1 second

Total analysis time with reports: **~35-65 seconds**

Still **10x faster** than manual review!

---

## Tips

### For Legal Teams
1. **Open Detailed Report** for complete analysis
2. Reference policy citations for justification
3. Use risk matrix for prioritization

### For Business Users
1. **Open HTML Summary** for quick overview
2. Filter to "Non-Compliant Only"
3. Focus on Critical/High risk items

### For Vendors
1. **Send Reviewed Contract** with track changes
2. Include summary section from Detailed Report
3. Highlight critical issues requiring attention

---

## Troubleshooting

### "Reports not generated"

Check that `output_path` is provided:
```python
results = analyzer.analyze_contract(
    contract_path="contract.docx",
    output_path="output.docx"  # Must provide this
)
```

### "HTML not displaying correctly"

Open in modern browser:
- Chrome ✅
- Firefox ✅
- Edge ✅
- Safari ✅

### "Word document formatting issues"

Ensure Microsoft Word 2016 or later for best compatibility.

---

**All reports are generated automatically - no extra configuration needed!** 🎉

Just run:
```bash
python main.py analyze your_contract.docx
```

And get 3 comprehensive reports showing everything the AI checked and changed!
