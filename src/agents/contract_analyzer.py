"""Contract analysis agent using Gemini and RAG."""

import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI

from ..core.config import settings
from ..core.prompts import (
    SYSTEM_PROMPT,
    CLAUSE_ANALYSIS_PROMPT,
    CONTRACT_SUMMARY_PROMPT
)
from ..document_processing import (
    DocxParser,
    ClauseExtractor,
    DocxGenerator,
    AnalysisReportGenerator
)
from .policy_checker import PolicyChecker
from .batch_contract_analyzer import BatchContractAnalyzer, SAFETY_SETTINGS

logger = logging.getLogger(__name__)


class ContractAnalyzer:
    """Main contract analysis agent coordinating all components."""

    def __init__(self, batch_mode: Optional[bool] = None, company_id: Optional[str] = None, region_code: Optional[str] = None):
        """
        Initialize the contract analyzer.

        Args:
            batch_mode: Enable batch processing (default: from settings)
            company_id: Optional company ID for user-specific policy checking
            region_code: Optional region code for regional knowledge base (e.g., "dubai_uae")
        """
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
            safety_settings=SAFETY_SETTINGS  # Prevent over-blocking of legal content
        )

        self.clause_extractor = ClauseExtractor()
        self.policy_checker = PolicyChecker(company_id=company_id, region_code=region_code)
        self.company_id = company_id
        self.region_code = region_code

        # Batch mode configuration
        self.batch_mode = batch_mode if batch_mode is not None else settings.batch_mode

        if self.batch_mode:
            self.batch_analyzer = BatchContractAnalyzer()
            logger.info(f"Initialized ContractAnalyzer (BATCH MODE){' for company: ' + company_id if company_id else ''}")
        else:
            logger.info(f"Initialized ContractAnalyzer (SINGLE-CLAUSE MODE){' for company: ' + company_id if company_id else ''}")

    def analyze_contract(
        self,
        contract_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a complete contract document.

        Args:
            contract_path: Path to the contract document
            output_path: Path for the output reviewed document

        Returns:
            Complete analysis results
        """
        logger.info(f"Starting contract analysis: {contract_path}")

        try:
            # 1. Parse the document
            parser = DocxParser(contract_path)
            doc_data = parser.extract_structured_content()

            # 2. Extract clauses
            clauses = self.clause_extractor.extract_clauses_from_paragraphs(
                doc_data["paragraphs"]
            )

            logger.info(f"Extracted {len(clauses)} clauses for analysis")

            # 3 & 4. Analyze clauses (batch or single-clause mode)
            if self.batch_mode and len(clauses) > 0:
                logger.info("🚀 Using BATCH MODE for analysis")

                # Dynamic token estimation based on clause complexity
                # Conservative estimate: 400-500 tokens per clause for complete analysis
                avg_tokens_per_clause = 450
                estimated_output_tokens = len(clauses) * avg_tokens_per_clause
                max_safe_tokens = int(settings.max_output_tokens * 0.85)  # Use 85% of limit for safety

                logger.info(f"Contract analysis estimation:")
                logger.info(f"  - Clauses to analyze: {len(clauses)}")
                logger.info(f"  - Estimated output tokens: ~{estimated_output_tokens:,}")
                logger.info(f"  - Max safe tokens: {max_safe_tokens:,}")
                logger.info(f"  - Configured limit: {settings.max_output_tokens:,}")

                # Use chunked analysis if needed
                if estimated_output_tokens > max_safe_tokens:
                    # Calculate optimal chunk size to stay within token limits
                    chunk_size = max(5, int(max_safe_tokens / avg_tokens_per_clause))
                    num_chunks = (len(clauses) + chunk_size - 1) // chunk_size

                    logger.warning(
                        f"⚠️ Contract exceeds token limit for single batch analysis!"
                    )
                    logger.warning(
                        f"  - Will split into {num_chunks} chunks of ~{chunk_size} clauses each"
                    )
                    logger.warning(
                        f"  - Consider increasing MAX_OUTPUT_TOKENS to {estimated_output_tokens * 1.2:.0f} for single-pass analysis"
                    )

                    batch_result = self.batch_analyzer.analyze_contract_chunked(
                        contract_text=doc_data["full_text"],
                        clauses=clauses,
                        chunk_size=chunk_size
                    )
                else:
                    # Single batch analysis - fits within token limits
                    logger.info(f"✅ Contract fits within token limits - using single batch")
                    batch_result = self.batch_analyzer.analyze_contract_batch(
                        contract_text=doc_data["full_text"],
                        clauses=clauses
                    )

                analysis_results = batch_result["analysis_results"]
                api_calls_used = batch_result.get("api_calls_used", 0)
                chunks_processed = batch_result.get("chunks_processed", 1)

                logger.info(
                    f"✅ Batch analysis complete: {api_calls_used} API calls, "
                    f"{chunks_processed} chunk(s) processed"
                )

            else:
                logger.info("⚙️ Using SINGLE-CLAUSE MODE for analysis")

                # Traditional single-clause analysis
                classified_clauses = self.clause_extractor.classify_all_clauses_sync(clauses)

                analysis_results = []
                for i, clause in enumerate(classified_clauses):
                    logger.info(f"Analyzing clause {i+1}/{len(classified_clauses)}")
                    result = self.analyze_single_clause(clause)
                    analysis_results.append(result)

            # 5. Generate contract summary
            summary = self.generate_contract_summary(
                contract_text=doc_data["full_text"],
                analysis_results=analysis_results
            )

            # 6. Generate output documents if requested
            if output_path:
                # Generate tracked changes document
                self.generate_review_document(
                    original_doc_path=contract_path,
                    analysis_results=analysis_results,
                    summary=summary,
                    output_path=output_path
                )

                # Generate detailed analysis report
                report_path = output_path.replace('.docx', '_DETAILED_REPORT.docx')
                html_report_path = output_path.replace('.docx', '_SUMMARY.html')

                logger.info("📊 Generating detailed analysis report...")
                report_generator = AnalysisReportGenerator()

                report_generator.generate_detailed_report(
                    analysis_results=analysis_results,
                    summary=summary,
                    contract_info=doc_data["properties"],
                    output_path=report_path
                )

                report_generator.generate_changes_summary_html(
                    analysis_results=analysis_results,
                    output_path=html_report_path
                )

                logger.info(f"✅ Reports generated:\n   - Reviewed: {output_path}\n   - Detailed: {report_path}\n   - HTML: {html_report_path}")

            logger.info("Contract analysis complete")

            return {
                "contract_info": doc_data["properties"],
                "summary": summary,
                "analysis_results": analysis_results,
                "statistics": {
                    "total_clauses": len(analysis_results),
                    "compliant": sum(1 for r in analysis_results if r.get("compliant")),
                    "non_compliant": sum(1 for r in analysis_results if not r.get("compliant"))
                },
                "output_files": {
                    "reviewed_contract": output_path if output_path else None,
                    "detailed_report": report_path if output_path else None,
                    "html_summary": html_report_path if output_path else None
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing contract: {e}")
            raise

    def analyze_single_clause(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single contract clause.

        Args:
            clause: Clause dictionary with text and classification

        Returns:
            Analysis result
        """
        try:
            clause_text = clause["text"]
            clause_type = clause.get("classification", {}).get("clause_type", "general")

            # Retrieve relevant policies
            retrieved_data = self.policy_checker.retrieve_relevant_policies(
                clause_text=clause_text,
                clause_type=clause_type,
                use_multi_query=True
            )

            # Format policies for the prompt
            formatted = self.policy_checker.format_policies_for_analysis(retrieved_data)

            # Analyze with Gemini
            prompt = CLAUSE_ANALYSIS_PROMPT.format(
                clause_text=clause_text,
                clause_type=clause_type,
                relevant_policies=formatted["policies_text"],
                relevant_laws=formatted["laws_text"]
            )

            response = self.llm.invoke(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            analysis = json.loads(response.content)

            # Merge with original clause data
            result = {
                **clause,
                **analysis,
                "retrieved_policies_count": len(retrieved_data["policies"]),
                "retrieved_laws_count": len(retrieved_data["laws"])
            }

            logger.debug(
                f"Clause analysis complete: {analysis.get('clause_type')} - "
                f"Compliant: {analysis.get('compliant')}"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing clause: {e}")
            return {
                **clause,
                "compliant": None,
                "error": str(e),
                "requires_human_review": True
            }

    def generate_contract_summary(
        self,
        contract_text: str,
        analysis_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate an executive summary of the contract analysis.

        Args:
            contract_text: Full contract text
            analysis_results: List of clause analysis results

        Returns:
            Contract summary
        """
        try:
            # Prepare analysis summary for prompt
            analysis_summary = self._format_analysis_for_summary(analysis_results)

            prompt = CONTRACT_SUMMARY_PROMPT.format(
                contract_text=contract_text[:5000],  # Limit context
                analysis_results=analysis_summary
            )

            response = self.llm.invoke(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            summary = json.loads(response.content)

            logger.info("Generated contract summary")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "contract_type": "Unknown",
                "overall_risk_assessment": "unknown",
                "error": str(e)
            }

    def _format_analysis_for_summary(
        self,
        analysis_results: List[Dict[str, Any]]
    ) -> str:
        """Format analysis results for summary generation."""
        summary_lines = []

        for result in analysis_results[:20]:  # Limit to first 20 clauses
            summary_lines.append(
                f"Clause: {result.get('clause_type', 'unknown')}\n"
                f"Compliant: {result.get('compliant', False)}\n"
                f"Risk: {result.get('risk_level', 'unknown')}\n"
            )

        return "\n".join(summary_lines)

    def generate_review_document(
        self,
        original_doc_path: str,
        analysis_results: List[Dict[str, Any]],
        summary: Dict[str, Any],
        output_path: str
    ):
        """
        Generate the final review document with track changes.

        Args:
            original_doc_path: Path to original document
            analysis_results: Analysis results
            summary: Contract summary
            output_path: Output path for reviewed document
        """
        try:
            generator = DocxGenerator(original_doc_path)

            # Add summary page
            generator.add_summary_page(summary)

            # Create review document with comments
            generator.create_review_document(
                analysis_results=analysis_results,
                output_path=output_path
            )

            logger.info(f"Generated review document: {output_path}")

        except Exception as e:
            logger.error(f"Error generating review document: {e}")
            raise

    def analyze_clause_text(
        self,
        clause_text: str,
        clause_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a single clause text (for testing or API use).

        Args:
            clause_text: The clause text
            clause_type: Optional clause type (will be classified if not provided)

        Returns:
            Analysis result
        """
        # Classify if type not provided
        if not clause_type:
            classification = self.clause_extractor.classify_clause_sync(clause_text)
            clause_type = classification.get("clause_type", "general")

        clause = {
            "clause_id": "single_clause",
            "text": clause_text,
            "classification": {
                "clause_type": clause_type
            }
        }

        return self.analyze_single_clause(clause)
