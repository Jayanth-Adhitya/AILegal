"""Batch contract analyzer - analyzes entire contract in minimal API calls."""

import logging
import json
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

from ..core.config import settings
from .smart_policy_retriever import SmartPolicyRetriever
from .rate_limit_handler import RateLimitHandler

logger = logging.getLogger(__name__)

# Safety settings to prevent over-blocking of legal content
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH
}


class BatchContractAnalyzer:
    """Analyze entire contract in a single batch API call."""

    def __init__(self, company_id: str = None, region_code: str = None):
        """
        Initialize batch analyzer.

        Args:
            company_id: Optional company ID for company-specific policies
            region_code: Optional region code for regional policies
        """
        # Use configured token limit for batch analysis (Gemini 2.0 Flash supports up to 65k)
        max_tokens = settings.max_output_tokens

        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=settings.temperature,
            max_output_tokens=max_tokens,
            safety_settings=SAFETY_SETTINGS  # Prevent over-blocking of legal content
        )

        logger.info(f"BatchAnalyzer initialized with max_output_tokens={max_tokens}")
        logger.info(f"Safety settings: BLOCK_ONLY_HIGH for all categories")

        self.policy_retriever = SmartPolicyRetriever(company_id=company_id, region_code=region_code)
        self.company_id = company_id
        self.region_code = region_code
        self.rate_limiter = RateLimitHandler(
            max_retries=getattr(settings, 'rate_limit_retry_attempts', 3)
        )

        logger.info(f"Initialized BatchContractAnalyzer{' for company: ' + company_id if company_id else ''}{' region: ' + region_code if region_code else ''}")

    def analyze_contract_batch(
        self,
        contract_text: str,
        clauses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze entire contract in a single batch operation.

        This reduces API calls from ~100 to ~3:
        1. Detect policy types + retrieve policies (via SmartPolicyRetriever)
        2. Analyze all clauses at once (this method)
        3. Generate summary (separate call)

        Args:
            contract_text: Full contract text
            clauses: List of extracted clause dictionaries

        Returns:
            Complete analysis results for all clauses
        """
        logger.info(f"Starting batch analysis for {len(clauses)} clauses")

        try:
            # Step 1: Get all relevant policies in one operation
            logger.info("📥 Retrieving all relevant policies...")
            policies_by_type = self.policy_retriever.get_all_relevant_policies_batch(
                contract_text=contract_text
            )

            # Optimize policies for context window
            policies_by_type = self.policy_retriever.optimize_policies_for_context_window(
                policies_by_type,
                max_tokens=500000  # Reserve 500k for policies
            )

            # Format policies
            formatted_policies = self.policy_retriever.format_policies_for_batch_prompt(
                policies_by_type
            )

            # Step 2: Analyze all clauses in single API call
            logger.info("🤖 Analyzing all clauses in batch...")
            analysis_results = self._analyze_all_clauses_batch(
                clauses=clauses,
                formatted_policies=formatted_policies
            )

            logger.info(f"✅ Batch analysis complete: {len(analysis_results)} clauses analyzed")

            return {
                "analysis_results": analysis_results,
                "policies_retrieved": sum(len(p) for p in policies_by_type.values()),
                "api_calls_used": 2  # 1 for policy detection, 1 for analysis
            }

        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            raise

    def _analyze_all_clauses_batch(
        self,
        clauses: List[Dict[str, Any]],
        formatted_policies: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze all clauses in a single API call.

        Args:
            clauses: List of clause dictionaries
            formatted_policies: Formatted policy text

        Returns:
            List of analysis results for each clause
        """
        # Build the batch analysis prompt
        batch_prompt = self._build_batch_analysis_prompt(
            clauses=clauses,
            formatted_policies=formatted_policies
        )

        # Execute with rate limiting and retry
        def api_call():
            logger.info(f"📤 Prompt length: {len(batch_prompt)} characters")
            logger.info(f"📤 Analyzing {len(clauses)} clauses")
            logger.info(f"📤 Max output tokens: {settings.max_output_tokens}")
            try:
                result = self.llm.invoke(
                    batch_prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "max_output_tokens": settings.max_output_tokens
                    },
                    timeout=180  # 3-minute timeout for large contracts
                )
                logger.info("✅ API call successful")
                return result
            except TimeoutError as e:
                logger.error(f"⏱️ API call timed out after 180 seconds")
                logger.error(f"Consider reducing batch size or increasing timeout")
                raise
            except Exception as e:
                logger.error(f"❌ API call failed: {type(e).__name__}: {str(e)}")
                raise

        logger.info("🚀 Sending batch analysis request to Gemini...")
        response = self.rate_limiter.execute_with_retry(api_call)

        # Log response details for debugging
        logger.info(f"📥 Received response from Gemini")
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response content length: {len(str(response.content))}")

        # Extract finish reason and metadata for diagnostics
        finish_reason = None
        safety_ratings = None
        token_usage = None

        if hasattr(response, 'response_metadata'):
            metadata = response.response_metadata
            logger.info(f"Response metadata: {metadata}")

            # Extract finish reason from various possible locations
            if isinstance(metadata, dict):
                # Direct finish_reason field
                if 'finish_reason' in metadata:
                    finish_reason = metadata['finish_reason']
                # Nested in candidates array
                elif 'candidates' in metadata and len(metadata['candidates']) > 0:
                    candidate = metadata['candidates'][0]
                    finish_reason = candidate.get('finishReason') or candidate.get('finish_reason')
                    safety_ratings = candidate.get('safetyRatings') or candidate.get('safety_ratings')

                # Extract token usage
                if 'usage_metadata' in metadata:
                    token_usage = metadata['usage_metadata']
                    logger.info(f"Token usage: {token_usage}")

            logger.info(f"Finish reason: {finish_reason}")
            if safety_ratings:
                logger.info(f"Safety ratings: {safety_ratings}")

        if hasattr(response, 'additional_kwargs'):
            logger.info(f"Additional kwargs: {response.additional_kwargs}")

        # Check for truncation due to token limits
        if finish_reason in ["MAX_TOKENS", "LENGTH"]:
            error_msg = f"⚠️ Response truncated due to token limit!\n"
            error_msg += f"Current limit: {settings.max_output_tokens} tokens\n"
            error_msg += f"Analyzed clauses: {len(clauses)}\n"
            if token_usage:
                error_msg += f"Token usage: {token_usage}\n"
            error_msg += f"SOLUTION: Increase MAX_OUTPUT_TOKENS or reduce batch size.\n"
            error_msg += f"Recommended: MAX_OUTPUT_TOKENS >= {len(clauses) * 400}"
            logger.error(error_msg)
            raise ValueError(f"Response truncated - MAX_TOKENS limit reached. {error_msg}")

        # Check for safety blocks
        if finish_reason == "SAFETY":
            error_msg = f"🚫 Response blocked by safety filters!\n"
            if safety_ratings:
                error_msg += f"Safety ratings: {safety_ratings}\n"
            error_msg += f"SOLUTION: Adjust safety settings or review contract content for triggering terms."
            logger.error(error_msg)
            raise ValueError(f"Safety filter blocked response. {error_msg}")

        # Check if response was blocked
        if not response.content or len(str(response.content).strip()) == 0:
            error_msg = "Gemini returned empty response. Possible causes:\n"
            error_msg += "1. Safety filters blocked the content\n"
            error_msg += "2. Response exceeded token limits\n"
            error_msg += "3. JSON generation failed\n"
            if hasattr(response, 'response_metadata'):
                error_msg += f"Metadata: {response.response_metadata}\n"
            logger.error(error_msg)
            raise ValueError("Empty response from Gemini API")

        # Parse response
        try:
            result = json.loads(response.content)
            analyses = result.get("clauses", [])

            # Merge with original clause data
            enriched_results = []
            for i, clause in enumerate(clauses):
                if i < len(analyses):
                    enriched_result = {
                        **clause,
                        **analyses[i]
                    }
                else:
                    # Fallback if analysis is missing
                    enriched_result = {
                        **clause,
                        "compliant": None,
                        "error": "Analysis not returned for this clause",
                        "requires_human_review": True
                    }

                enriched_results.append(enriched_result)

            return enriched_results

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON PARSING FAILED: {e}")
            logger.error(f"Error details: {str(e)}")
            logger.error(f"Response content preview (first 1000 chars):\n{response.content[:1000]}")
            logger.error(f"Response content preview (last 500 chars):\n{response.content[-500:]}")

            # Provide actionable error message
            error_msg = f"Failed to parse Gemini response as JSON.\n"
            error_msg += f"Error: {str(e)}\n"
            error_msg += f"This usually means the response was truncated mid-string.\n"
            error_msg += f"Current MAX_OUTPUT_TOKENS: {settings.max_output_tokens}\n"
            error_msg += f"Number of clauses: {len(clauses)}\n"
            error_msg += f"Recommended: Increase MAX_OUTPUT_TOKENS to at least {len(clauses) * 500}"

            raise ValueError(error_msg) from e

    def _build_batch_analysis_prompt(
        self,
        clauses: List[Dict[str, Any]],
        formatted_policies: str
    ) -> str:
        """
        Build the comprehensive batch analysis prompt.

        Args:
            clauses: List of clauses to analyze
            formatted_policies: Formatted policy documents

        Returns:
            Complete prompt for batch analysis
        """
        # Format clauses for the prompt
        clauses_text = self._format_clauses_for_prompt(clauses)

        prompt = f"""You are an AI Legal Assistant analyzing a contract against company policies.

TASK: Analyze ALL {len(clauses)} clauses in this contract and return a comprehensive JSON analysis.

COMPANY POLICIES:
{formatted_policies}

CONTRACT CLAUSES TO ANALYZE:
{clauses_text}

INSTRUCTIONS:
1. For EACH clause, determine:
   - Clause type (liability, IP, payment_terms, etc.)
   - Compliance status (true/false)
   - Risk level (low/medium/high/critical)
   - Specific issues found
   - Redline suggestions for non-compliant clauses
   - Policy citations

2. Be thorough but concise in your analysis
3. Always cite specific policy references
4. Provide actionable redline suggestions for non-compliant clauses

OUTPUT FORMAT:
Return a JSON object with this EXACT structure (use simple strings for arrays, no nested objects):

{{
  "clauses": [
    {{
      "clause_id": "clause_1",
      "clause_type": "liability",
      "compliant": true,
      "risk_level": "low",
      "issues": ["issue 1", "issue 2"],
      "recommendations": ["recommendation 1", "recommendation 2"],
      "policy_references": ["policy 1", "policy 2"],
      "suggested_alternative": "suggested wording if non-compliant, empty string if compliant"
    }},
    {{
      "clause_id": "clause_2",
      "clause_type": "payment_terms",
      "compliant": false,
      "risk_level": "high",
      "issues": ["Payment terms exceed 30 days"],
      "recommendations": ["Reduce payment terms to Net 30"],
      "policy_references": ["Company Payment Policy Section 2.1"],
      "suggested_alternative": "Payment due within 30 days of invoice date"
    }}
  ]
}}

IMPORTANT RULES:
- All array fields must contain strings only (no nested objects)
- Return analysis for ALL {len(clauses)} clauses
- Keep same order as input
- Use empty arrays [] if no issues/recommendations
- Use empty string "" for suggested_alternative if compliant

IMPORTANT:
- Analyze ALL {len(clauses)} clauses
- Return analysis in the SAME ORDER as clauses provided
- Include clause_id matching the input
- Be consistent with risk assessments
- Cite policies precisely

Begin analysis:
"""

        return prompt

    def _format_clauses_for_prompt(
        self,
        clauses: List[Dict[str, Any]]
    ) -> str:
        """
        Format clauses for inclusion in prompt.

        Args:
            clauses: List of clause dictionaries

        Returns:
            Formatted string
        """
        formatted = []

        for clause in clauses:
            formatted.append(
                f"\n{'='*80}\n"
                f"CLAUSE ID: {clause.get('clause_id', 'unknown')}\n"
                f"PARAGRAPH INDEX: {clause.get('paragraph_index', 'N/A')}\n"
                f"TEXT:\n{clause.get('text', '')}\n"
                f"{'='*80}\n"
            )

        return "\n".join(formatted)

    def estimate_prompt_tokens(
        self,
        clauses: List[Dict[str, Any]],
        formatted_policies: str
    ) -> int:
        """
        Estimate total tokens for the batch prompt.

        Args:
            clauses: List of clauses
            formatted_policies: Formatted policies

        Returns:
            Approximate token count
        """
        clauses_text = self._format_clauses_for_prompt(clauses)
        total_text = formatted_policies + clauses_text

        # Rough estimate: 4 chars per token
        estimated_tokens = len(total_text) // 4

        logger.info(f"Estimated prompt size: ~{estimated_tokens:,} tokens")

        return estimated_tokens

    def should_chunk_contract(
        self,
        clauses: List[Dict[str, Any]],
        formatted_policies: str,
        max_tokens: int = 900000  # Leave room for response
    ) -> bool:
        """
        Determine if contract should be chunked.

        Args:
            clauses: List of clauses
            formatted_policies: Formatted policies
            max_tokens: Maximum tokens for prompt

        Returns:
            True if chunking is needed
        """
        estimated = self.estimate_prompt_tokens(clauses, formatted_policies)

        if estimated > max_tokens:
            logger.warning(
                f"Contract too large: ~{estimated:,} tokens > {max_tokens:,}. "
                "Chunking required."
            )
            return True

        return False

    def analyze_contract_chunked(
        self,
        contract_text: str,
        clauses: List[Dict[str, Any]],
        chunk_size: int = 25
    ) -> Dict[str, Any]:
        """
        Analyze contract in chunks if it's too large.

        Args:
            contract_text: Full contract text
            clauses: List of clauses
            chunk_size: Number of clauses per chunk

        Returns:
            Combined analysis results
        """
        logger.info(f"Chunking {len(clauses)} clauses into groups of {chunk_size}")

        # Get policies once
        policies_by_type = self.policy_retriever.get_all_relevant_policies_batch(
            contract_text=contract_text
        )
        formatted_policies = self.policy_retriever.format_policies_for_batch_prompt(
            policies_by_type
        )

        # Process in chunks
        all_results = []
        num_chunks = (len(clauses) + chunk_size - 1) // chunk_size

        for i in range(0, len(clauses), chunk_size):
            chunk = clauses[i:i + chunk_size]
            chunk_num = (i // chunk_size) + 1

            logger.info(f"Processing chunk {chunk_num}/{num_chunks} ({len(chunk)} clauses)")

            chunk_results = self._analyze_all_clauses_batch(
                clauses=chunk,
                formatted_policies=formatted_policies
            )

            all_results.extend(chunk_results)

        return {
            "analysis_results": all_results,
            "policies_retrieved": sum(len(p) for p in policies_by_type.values()),
            "api_calls_used": num_chunks + 1,  # 1 for policies + chunks
            "chunks_processed": num_chunks
        }
