"""
AI Legal Assistant - Command Line Interface

Simple CLI tool to analyze contracts without using the API.
"""

import sys
import logging
from pathlib import Path
import argparse

from src.agents.contract_analyzer import ContractAnalyzer
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="AI Legal Assistant - Automated Contract Review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a contract
  python main.py analyze contract.docx

  # Specify output path
  python main.py analyze contract.docx -o reviewed_contract.docx

  # Analyze a single clause
  python main.py clause "The Company shall not be liable for any damages."
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Analyze contract command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a contract document")
    analyze_parser.add_argument("contract", help="Path to contract file (.docx)")
    analyze_parser.add_argument(
        "-o", "--output",
        help="Output path for reviewed document (default: auto-generated)"
    )

    # Analyze clause command
    clause_parser = subparsers.add_parser("clause", help="Analyze a single clause")
    clause_parser.add_argument("text", help="Clause text to analyze")
    clause_parser.add_argument(
        "-t", "--type",
        help="Clause type (e.g., liability, payment_terms)"
    )

    # Stats command
    subparsers.add_parser("stats", help="Show vector store statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print("=" * 70)
    print("🤖 AI Legal Assistant - Powered by Gemini 2.5 Flash")
    print("=" * 70)
    print()

    try:
        if args.command == "analyze":
            analyze_contract(args.contract, args.output)

        elif args.command == "clause":
            analyze_clause(args.text, args.type)

        elif args.command == "stats":
            show_stats()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def analyze_contract(contract_path: str, output_path: str = None):
    """Analyze a contract document."""
    contract_file = Path(contract_path)

    if not contract_file.exists():
        print(f"❌ Contract file not found: {contract_path}")
        return

    if not contract_file.suffix == ".docx":
        print(f"❌ Only .docx files are supported. Got: {contract_file.suffix}")
        return

    # Generate output path if not provided
    if not output_path:
        output_path = contract_file.parent / f"{contract_file.stem}_reviewed.docx"

    print(f"📄 Contract: {contract_file.name}")
    print(f"📝 Output: {Path(output_path).name}")
    print()
    print("🔍 Analyzing contract...")
    print()

    # Initialize analyzer
    analyzer = ContractAnalyzer()

    # Analyze
    results = analyzer.analyze_contract(
        contract_path=str(contract_file),
        output_path=str(output_path)
    )

    # Print summary
    summary = results["summary"]
    stats = results["statistics"]

    print()
    print("=" * 70)
    print("📊 Analysis Complete!")
    print("=" * 70)
    print()

    print(f"📋 Contract Type: {summary.get('contract_type', 'Unknown')}")
    print(f"📈 Total Clauses: {stats['total_clauses']}")
    print(f"✅ Compliant: {stats['compliant']}")
    print(f"❌ Non-Compliant: {stats['non_compliant']}")
    print()

    risk = summary.get('overall_risk_assessment', 'unknown').upper()
    risk_emoji = {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🔴",
        "CRITICAL": "🚨"
    }
    print(f"{risk_emoji.get(risk, '⚪')} Risk Level: {risk}")
    print()

    if summary.get('recommendation'):
        print(f"💡 Recommendation:")
        print(f"   {summary['recommendation']}")
        print()

    if summary.get('critical_issues'):
        print(f"⚠️  Critical Issues: {len(summary['critical_issues'])}")
        for issue in summary['critical_issues'][:3]:
            print(f"   - {issue.get('issue', 'Unknown issue')}")
        print()

    # Show output files
    print("💾 Generated Files:")
    print()

    if "output_files" in results:
        output_files = results["output_files"]

        if output_files.get("reviewed_contract"):
            print(f"   📝 Reviewed Contract (with track changes):")
            print(f"      {Path(output_files['reviewed_contract']).absolute()}")
            print()

        if output_files.get("detailed_report"):
            print(f"   📊 Detailed Analysis Report (Word document):")
            print(f"      {Path(output_files['detailed_report']).absolute()}")
            print(f"      → Open this to see all clauses checked and changes recommended")
            print()

        if output_files.get("html_summary"):
            print(f"   🌐 Interactive HTML Summary (open in browser):")
            print(f"      {Path(output_files['html_summary']).absolute()}")
            print(f"      → Filterable view of all analysis results")
            print()
    else:
        print(f"   {Path(output_path).absolute()}")
        print()

    print("✅ Open the Detailed Report to see:")
    print("   • Every clause that was analyzed")
    print("   • What issues were found")
    print("   • Recommended changes for each non-compliant clause")
    print("   • Policy references and citations")
    print()
    print("💡 TIP: Open the HTML file in your browser for an interactive view!")


def analyze_clause(clause_text: str, clause_type: str = None):
    """Analyze a single clause."""
    print(f"📝 Analyzing clause...")
    print()
    print(f"Clause: {clause_text[:100]}...")
    if clause_type:
        print(f"Type: {clause_type}")
    print()

    # Initialize analyzer
    analyzer = ContractAnalyzer()

    # Analyze
    result = analyzer.analyze_clause_text(
        clause_text=clause_text,
        clause_type=clause_type
    )

    # Print result
    print("=" * 70)
    print("📊 Analysis Result")
    print("=" * 70)
    print()

    print(f"🏷️  Clause Type: {result.get('classification', {}).get('clause_type', 'Unknown')}")
    print(f"✓  Compliant: {'Yes' if result.get('compliant') else 'No'}")
    print(f"⚠️  Risk Level: {result.get('risk_level', 'Unknown').upper()}")
    print()

    if not result.get('compliant'):
        print(f"❌ Issues Found:")
        for issue in result.get('issues', []):
            print(f"   - {issue.get('issue_description', 'Unknown')}")
            print(f"     Policy: {issue.get('policy_reference', 'N/A')}")
            print()

        if result.get('redline_suggestion'):
            print(f"💡 Suggested Alternative:")
            print(f"   {result['redline_suggestion']}")
            print()

    if result.get('policy_citations'):
        print(f"📚 Policy References:")
        for citation in result['policy_citations']:
            print(f"   - {citation}")
        print()


def show_stats():
    """Show vector store statistics."""
    from src.vector_store.embeddings import PolicyEmbeddings

    print("📊 Vector Store Statistics")
    print()

    embeddings = PolicyEmbeddings()
    stats = embeddings.get_collection_stats()

    print(f"Collection: {stats['collection_name']}")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Embedding Model: {stats['embedding_model']}")
    print()

    if stats['total_documents'] == 0:
        print("⚠️  No policies ingested yet!")
        print()
        print("Run: python -m src.scripts.ingest_policies")


if __name__ == "__main__":
    main()
