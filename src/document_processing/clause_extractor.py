"""Extract and classify contract clauses."""

import logging
import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

from ..core.config import settings
from ..core.prompts import CLAUSE_TYPE_CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)


class ClauseExtractor:
    """Extract and classify clauses from contract text."""

    def __init__(self):
        """Initialize clause extractor with Gemini model."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=settings.temperature
        )
        logger.info("Initialized ClauseExtractor")

    def extract_clauses_from_sections(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract clauses from document sections.

        Args:
            sections: List of document sections from parser

        Returns:
            List of extracted clauses with metadata
        """
        clauses = []

        for section in sections:
            # Each section content paragraph is treated as a potential clause
            for content in section.get("content", []):
                clause = {
                    "clause_id": f"clause_{content['index']}",
                    "text": content["text"],
                    "section_heading": section["heading"],
                    "paragraph_index": content["index"]
                }
                clauses.append(clause)

        logger.info(f"Extracted {len(clauses)} clauses from sections")
        return clauses

    def extract_clauses_from_paragraphs(
        self,
        paragraphs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract clauses from document paragraphs.

        Args:
            paragraphs: List of paragraphs from parser

        Returns:
            List of clauses
        """
        clauses = []

        for para in paragraphs:
            # Skip headings
            if para.get("is_heading"):
                continue

            # Filter out very short paragraphs (likely not clauses)
            if len(para["text"].split()) < 10:
                continue

            clause = {
                "clause_id": f"clause_{para['index']}",
                "text": para["text"],
                "paragraph_index": para["index"],
                "style": para["style"]
            }
            clauses.append(clause)

        logger.info(f"Extracted {len(clauses)} clauses from paragraphs")
        return clauses

    async def classify_clause(self, clause_text: str) -> Dict[str, Any]:
        """
        Classify a single clause using Gemini.

        Args:
            clause_text: The clause text to classify

        Returns:
            Classification result with type and confidence
        """
        try:
            prompt = CLAUSE_TYPE_CLASSIFIER_PROMPT.format(clause_text=clause_text)

            response = await self.llm.ainvoke(
                prompt,
                generation_config={
                    "response_mime_type": "application/json"
                }
            )

            result = json.loads(response.content)
            logger.debug(f"Classified clause as: {result.get('clause_type')}")
            return result

        except Exception as e:
            logger.error(f"Error classifying clause: {e}")
            return {
                "clause_type": "general",
                "secondary_types": [],
                "confidence": 0.0,
                "key_phrases": []
            }

    def classify_clause_sync(self, clause_text: str) -> Dict[str, Any]:
        """
        Classify a single clause using Gemini (synchronous version).

        Args:
            clause_text: The clause text to classify

        Returns:
            Classification result with type and confidence
        """
        try:
            prompt = CLAUSE_TYPE_CLASSIFIER_PROMPT.format(clause_text=clause_text)

            response = self.llm.invoke(
                prompt,
                generation_config={
                    "response_mime_type": "application/json"
                }
            )

            result = json.loads(response.content)
            logger.debug(f"Classified clause as: {result.get('clause_type')}")
            return result

        except Exception as e:
            logger.error(f"Error classifying clause: {e}")
            return {
                "clause_type": "general",
                "secondary_types": [],
                "confidence": 0.0,
                "key_phrases": []
            }

    async def classify_all_clauses(
        self,
        clauses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Classify all clauses in a contract.

        Args:
            clauses: List of extracted clauses

        Returns:
            Clauses with classification information added
        """
        classified_clauses = []

        for clause in clauses:
            classification = await self.classify_clause(clause["text"])

            classified_clause = {
                **clause,
                "classification": classification
            }
            classified_clauses.append(classified_clause)

        logger.info(f"Classified {len(classified_clauses)} clauses")
        return classified_clauses

    def classify_all_clauses_sync(
        self,
        clauses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Classify all clauses in a contract (synchronous version).

        Args:
            clauses: List of extracted clauses

        Returns:
            Clauses with classification information added
        """
        classified_clauses = []

        for i, clause in enumerate(clauses):
            logger.info(f"Classifying clause {i+1}/{len(clauses)}")
            classification = self.classify_clause_sync(clause["text"])

            classified_clause = {
                **clause,
                "classification": classification
            }
            classified_clauses.append(classified_clause)

        logger.info(f"Classified {len(classified_clauses)} clauses")
        return classified_clauses

    def group_clauses_by_type(
        self,
        classified_clauses: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group clauses by their classification type.

        Args:
            classified_clauses: List of classified clauses

        Returns:
            Dictionary mapping clause types to lists of clauses
        """
        grouped = {}

        for clause in classified_clauses:
            clause_type = clause.get("classification", {}).get("clause_type", "general")

            if clause_type not in grouped:
                grouped[clause_type] = []

            grouped[clause_type].append(clause)

        logger.info(f"Grouped clauses into {len(grouped)} types")
        return grouped

    def get_clause_summary(
        self,
        classified_clauses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a summary of clause types and distribution.

        Args:
            classified_clauses: List of classified clauses

        Returns:
            Summary statistics
        """
        grouped = self.group_clauses_by_type(classified_clauses)

        summary = {
            "total_clauses": len(classified_clauses),
            "clause_types": {
                clause_type: len(clauses)
                for clause_type, clauses in grouped.items()
            },
            "most_common_type": max(grouped.items(), key=lambda x: len(x[1]))[0] if grouped else None
        }

        logger.info(f"Generated clause summary: {summary['total_clauses']} clauses")
        return summary
