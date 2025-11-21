"""Policy checking agent using RAG."""

import logging
import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

from ..core.config import settings
from ..core.prompts import POLICY_RETRIEVAL_QUERY_PROMPT
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


class PolicyChecker:
    """Check contract clauses against company policies using RAG."""

    def __init__(self, company_id: str = None, region_code: str = None):
        """
        Initialize policy checker with retriever and LLM.

        Args:
            company_id: Optional company ID for user-specific policy retrieval
            region_code: Optional region code for regional knowledge base (e.g., "dubai_uae")
        """
        self.retriever = PolicyRetriever(company_id=company_id)
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=settings.temperature,
            safety_settings=SAFETY_SETTINGS
        )
        self.company_id = company_id
        self.region_code = region_code
        logger.info(f"Initialized PolicyChecker{' for company: ' + company_id if company_id else ''}{' region: ' + region_code if region_code else ''}")

    async def generate_retrieval_queries(
        self,
        clause_text: str,
        clause_type: str
    ) -> List[str]:
        """
        Generate multiple search queries for better policy retrieval.

        Args:
            clause_text: The contract clause
            clause_type: Type of the clause

        Returns:
            List of search queries
        """
        try:
            prompt = POLICY_RETRIEVAL_QUERY_PROMPT.format(
                clause_text=clause_text,
                clause_type=clause_type
            )

            response = await self.llm.ainvoke(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            result = json.loads(response.content)
            queries = result.get("queries", [clause_text])

            logger.debug(f"Generated {len(queries)} retrieval queries")
            return queries

        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            return [clause_text]  # Fallback to original clause

    def generate_retrieval_queries_sync(
        self,
        clause_text: str,
        clause_type: str
    ) -> List[str]:
        """
        Generate multiple search queries (synchronous version).

        Args:
            clause_text: The contract clause
            clause_type: Type of the clause

        Returns:
            List of search queries
        """
        try:
            prompt = POLICY_RETRIEVAL_QUERY_PROMPT.format(
                clause_text=clause_text,
                clause_type=clause_type
            )

            response = self.llm.invoke(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            result = json.loads(response.content)
            queries = result.get("queries", [clause_text])

            logger.debug(f"Generated {len(queries)} retrieval queries")
            return queries

        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            return [clause_text]

    def retrieve_relevant_policies(
        self,
        clause_text: str,
        clause_type: str,
        use_multi_query: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve relevant policies for a clause.

        Args:
            clause_text: The contract clause
            clause_type: Type of the clause
            use_multi_query: Whether to use multiple queries

        Returns:
            Dictionary with policies and laws
        """
        try:
            # Use regional-aware retrieval
            # For simplicity, we use single region-aware query even in multi-query mode
            # This provides both global and regional documents
            all_policies = self.retriever.retrieve_with_region(
                query=clause_text,
                region_code=self.region_code,
                n_results=settings.retrieval_k if not use_multi_query else settings.retrieval_k * 2
            )

            # Separate policies, laws, and regional documents based on metadata
            policies = []
            laws = []
            regional_docs = []

            for policy in all_policies:
                source_type = policy["metadata"].get("source_type", "policy")
                if source_type == "regional":
                    regional_docs.append(policy)
                elif source_type == "law":
                    laws.append(policy)
                else:
                    policies.append(policy)

            logger.info(f"Retrieved {len(policies)} policies, {len(laws)} laws, and {len(regional_docs)} regional documents")

            return {
                "policies": policies,
                "laws": laws,
                "regional_documents": regional_docs,
                "all_documents": all_policies
            }

        except Exception as e:
            logger.error(f"Error retrieving policies: {e}")
            return {"policies": [], "laws": [], "all_documents": []}

    def format_policies_for_analysis(
        self,
        retrieved_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Format retrieved policies for LLM consumption.

        Args:
            retrieved_data: Retrieved policies and laws

        Returns:
            Formatted strings for policies and laws
        """
        policies_text = self.retriever.format_policies_for_prompt(
            retrieved_data.get("policies", [])
        )

        laws_text = self.retriever.format_policies_for_prompt(
            retrieved_data.get("laws", [])
        )

        return {
            "policies_text": policies_text,
            "laws_text": laws_text
        }

    def get_policy_by_section(
        self,
        clause_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get policies by exact section match.

        Args:
            clause_type: The type of clause

        Returns:
            Matching policies
        """
        # Map clause types to policy sections
        section_mapping = {
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

        section = section_mapping.get(clause_type, "general")

        policies = self.retriever.get_policy_by_exact_match(
            policy_type="Legal",
            section=section
        )

        logger.info(f"Retrieved {len(policies)} policies for section: {section}")
        return policies

    def check_clause_compliance(
        self,
        clause_text: str,
        clause_type: str,
        policies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if a clause complies with policies.

        Args:
            clause_text: The contract clause
            clause_type: Type of clause
            policies: List of relevant policies

        Returns:
            Compliance check result
        """
        # This is a simplified compliance check
        # The actual analysis is done by the ContractAnalyzer

        if not policies:
            return {
                "requires_review": True,
                "reason": "No relevant policies found for comparison"
            }

        return {
            "policies_found": len(policies),
            "ready_for_analysis": True
        }
