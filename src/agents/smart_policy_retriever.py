"""Smart policy retrieval for batch contract analysis."""

import logging
import json
from typing import List, Dict, Any, Set
from langchain_google_genai import ChatGoogleGenerativeAI

from ..core.config import settings
from ..vector_store.retriever import PolicyRetriever

logger = logging.getLogger(__name__)

# Safety settings to prevent over-blocking of legal content
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH"
    }
]


class SmartPolicyRetriever:
    """Intelligently retrieve all relevant policies for a contract in one go."""

    def __init__(self):
        """Initialize smart retriever."""
        self.retriever = PolicyRetriever()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.1,
            safety_settings=SAFETY_SETTINGS
        )
        logger.info("Initialized SmartPolicyRetriever")

    def detect_policy_types_from_contract(
        self,
        contract_preview: str
    ) -> Set[str]:
        """
        Detect what types of policies are needed based on contract preview.

        Args:
            contract_preview: First ~5000 chars of contract

        Returns:
            Set of policy types needed
        """
        try:
            prompt = f"""Analyze this contract preview and identify which policy types are relevant.

CONTRACT PREVIEW:
{contract_preview[:5000]}

Available policy types:
- liability
- intellectual_property
- payment_terms
- termination
- confidentiality
- warranty
- dispute_resolution
- delivery
- data_protection
- compliance

Return JSON with list of relevant policy types:
{{
  "policy_types": ["type1", "type2", ...]
}}
"""

            response = self.llm.invoke(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            result = json.loads(response.content)
            policy_types = set(result.get("policy_types", []))

            logger.info(f"Detected {len(policy_types)} policy types: {policy_types}")
            return policy_types

        except Exception as e:
            logger.error(f"Error detecting policy types: {e}")
            # Fallback: return all types
            return {
                "liability", "intellectual_property", "payment_terms",
                "termination", "confidentiality", "warranty",
                "dispute_resolution", "delivery", "data_protection", "compliance"
            }

    def get_all_relevant_policies_batch(
        self,
        contract_text: str,
        n_results_per_type: int = 3
    ) -> Dict[str, Any]:
        """
        Get all relevant policies for a contract in a single batch operation.

        Args:
            contract_text: Full contract text or preview
            n_results_per_type: Number of policy documents per type

        Returns:
            Dictionary with policies organized by type
        """
        try:
            # Step 1: Detect needed policy types
            contract_preview = contract_text[:10000]  # Use first 10k chars
            policy_types = self.detect_policy_types_from_contract(contract_preview)

            logger.info(f"Retrieving policies for {len(policy_types)} types")

            # Step 2: Retrieve policies for each type
            all_policies = {}
            policy_type_mapping = {
                "liability": "Liability",
                "intellectual_property": "IP",
                "payment_terms": "PaymentTerms",
                "termination": "Termination",
                "confidentiality": "Confidentiality",
                "warranty": "Warranty",
                "dispute_resolution": "DisputeResolution",
                "delivery": "Delivery",
                "data_protection": "DataProtection",
                "compliance": "Compliance"
            }

            for policy_type in policy_types:
                section = policy_type_mapping.get(policy_type, "general")

                try:
                    # Create a general query for this type
                    query = f"{policy_type.replace('_', ' ')} policy requirements standards"

                    policies = self.retriever.retrieve_relevant_policies(
                        query=query,
                        n_results=n_results_per_type,
                        filter_metadata={"section": section}
                    )

                    # If no results with filter, try without filter
                    if not policies:
                        policies = self.retriever.retrieve_relevant_policies(
                            query=query,
                            n_results=n_results_per_type
                        )

                    all_policies[policy_type] = policies
                    logger.debug(f"Retrieved {len(policies)} policies for {policy_type}")

                except Exception as e:
                    logger.warning(f"Error retrieving policies for {policy_type}: {e}")
                    all_policies[policy_type] = []

            # Step 3: Also get general/catch-all policies
            general_policies = self.retriever.retrieve_relevant_policies(
                query=contract_preview[:2000],
                n_results=5
            )
            all_policies["general"] = general_policies

            total_policies = sum(len(p) for p in all_policies.values())
            logger.info(f"Retrieved {total_policies} total policy documents")

            return all_policies

        except Exception as e:
            logger.error(f"Error in batch policy retrieval: {e}")
            return {}

    def format_policies_for_batch_prompt(
        self,
        policies_by_type: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """
        Format retrieved policies for batch analysis prompt.

        Args:
            policies_by_type: Policies organized by type

        Returns:
            Formatted string for LLM prompt
        """
        if not policies_by_type:
            return "No relevant policies found."

        formatted_sections = []

        for policy_type, policies in policies_by_type.items():
            if not policies:
                continue

            section_header = f"\n{'='*80}\n{policy_type.upper().replace('_', ' ')} POLICIES\n{'='*80}\n"
            formatted_sections.append(section_header)

            for i, policy in enumerate(policies, 1):
                metadata = policy["metadata"]
                formatted_sections.append(
                    f"\n**Policy {policy_type}_{i}:**\n"
                    f"Type: {metadata.get('policy_type', 'Unknown')}\n"
                    f"Section: {metadata.get('section', 'Unknown')}\n"
                    f"Version: {metadata.get('version', 'Unknown')}\n"
                    f"Relevance: {policy['similarity_score']:.2%}\n\n"
                    f"{policy['content']}\n"
                    f"{'-' * 80}\n"
                )

        return "\n".join(formatted_sections)

    def get_compact_policy_summary(
        self,
        policies_by_type: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, str]:
        """
        Get a compact summary of policies for quick reference.

        Args:
            policies_by_type: Policies organized by type

        Returns:
            Dictionary mapping policy types to key requirements
        """
        summary = {}

        for policy_type, policies in policies_by_type.items():
            if not policies:
                continue

            # Extract key points from top policy
            top_policy = policies[0]
            content = top_policy["content"]

            # Simple extraction of first few sentences
            sentences = content.split('.')[:3]
            summary[policy_type] = '. '.join(sentences) + '.'

        return summary

    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Approximate token count
        """
        # Rough estimate: ~4 chars per token
        return len(text) // 4

    def optimize_policies_for_context_window(
        self,
        policies_by_type: Dict[str, List[Dict[str, Any]]],
        max_tokens: int = 500000
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Optimize policy set to fit within context window.

        Args:
            policies_by_type: Policies organized by type
            max_tokens: Maximum tokens to use for policies

        Returns:
            Optimized policy set
        """
        # Format policies
        formatted = self.format_policies_for_batch_prompt(policies_by_type)
        current_tokens = self.estimate_token_count(formatted)

        if current_tokens <= max_tokens:
            logger.info(f"Policies fit in context: ~{current_tokens} tokens")
            return policies_by_type

        logger.warning(f"Policies exceed limit: ~{current_tokens} > {max_tokens}")

        # Reduce policies per type
        optimized = {}
        for policy_type, policies in policies_by_type.items():
            # Keep top 2 most relevant for each type
            optimized[policy_type] = policies[:2]

        formatted_optimized = self.format_policies_for_batch_prompt(optimized)
        optimized_tokens = self.estimate_token_count(formatted_optimized)

        logger.info(f"Optimized to ~{optimized_tokens} tokens")
        return optimized
