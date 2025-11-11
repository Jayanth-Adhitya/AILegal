"""Policy retrieval using semantic search."""

import logging
from typing import List, Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import chromadb
from chromadb.config import Settings as ChromaSettings

from ..core.config import settings

logger = logging.getLogger(__name__)


class PolicyRetriever:
    """Retrieves relevant policies using semantic search."""

    def __init__(self, collection_name: Optional[str] = None, company_id: Optional[str] = None):
        """
        Initialize retriever with embeddings and ChromaDB.

        Args:
            collection_name: Optional specific collection name to use
            company_id: Optional company ID to use for user-specific collection
        """
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key
        )

        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Determine collection name
        if company_id:
            self.collection_name = f"policies_{company_id}"
        elif collection_name:
            self.collection_name = collection_name
        else:
            self.collection_name = settings.chroma_collection_name

        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Connected to collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to get collection: {e}")
            raise

    def retrieve_relevant_policies(
        self,
        query: str,
        n_results: int = None,
        filter_metadata: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant policies for a given query.

        Args:
            query: The search query (usually a contract clause)
            n_results: Number of results to return (default from settings)
            filter_metadata: Optional metadata filters (e.g., {"policy_type": "Legal"})

        Returns:
            List of relevant policy documents with metadata and scores
        """
        if n_results is None:
            n_results = settings.retrieval_k

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Query ChromaDB
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"]
            }

            # Add metadata filter if provided
            if filter_metadata:
                query_params["where"] = filter_metadata

            results = self.collection.query(**query_params)

            # Format results
            formatted_results = []
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "distance": results["distances"][0][i]
                })

            logger.info(f"Retrieved {len(formatted_results)} relevant policies")
            return formatted_results

        except Exception as e:
            logger.error(f"Error retrieving policies: {e}")
            raise

    def retrieve_by_policy_type(
        self,
        query: str,
        policy_type: str,
        n_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve policies filtered by type.

        Args:
            query: The search query
            policy_type: Type of policy to retrieve ("Legal", "Commercial", etc.)
            n_results: Number of results

        Returns:
            List of relevant policies of the specified type
        """
        return self.retrieve_relevant_policies(
            query=query,
            n_results=n_results,
            filter_metadata={"policy_type": policy_type}
        )

    def retrieve_by_section(
        self,
        query: str,
        section: str,
        n_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve policies filtered by section.

        Args:
            query: The search query
            section: Policy section (e.g., "Liability", "PaymentTerms")
            n_results: Number of results

        Returns:
            List of relevant policies from the specified section
        """
        return self.retrieve_relevant_policies(
            query=query,
            n_results=n_results,
            filter_metadata={"section": section}
        )

    def retrieve_multi_query(
        self,
        queries: List[str],
        n_results_per_query: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Retrieve policies using multiple queries and merge results.

        Args:
            queries: List of search queries
            n_results_per_query: Number of results per query

        Returns:
            Deduplicated list of relevant policies
        """
        all_results = []
        seen_ids = set()

        for query in queries:
            results = self.retrieve_relevant_policies(
                query=query,
                n_results=n_results_per_query
            )

            for result in results:
                # Create a unique ID based on content hash
                content_id = hash(result["content"])

                if content_id not in seen_ids:
                    seen_ids.add(content_id)
                    all_results.append(result)

        # Sort by similarity score
        all_results.sort(key=lambda x: x["similarity_score"], reverse=True)

        logger.info(f"Retrieved {len(all_results)} unique policies from {len(queries)} queries")
        return all_results

    def format_policies_for_prompt(self, policies: List[Dict[str, Any]]) -> str:
        """
        Format retrieved policies for inclusion in LLM prompts.

        Args:
            policies: List of policy documents

        Returns:
            Formatted string for prompt
        """
        if not policies:
            return "No relevant policies found."

        formatted = []
        for i, policy in enumerate(policies, 1):
            metadata = policy["metadata"]
            formatted.append(
                f"**Policy {i}:**\n"
                f"Type: {metadata.get('policy_type', 'Unknown')}\n"
                f"Section: {metadata.get('section', 'Unknown')}\n"
                f"Version: {metadata.get('version', 'Unknown')}\n"
                f"Relevance: {policy['similarity_score']:.2%}\n\n"
                f"{policy['content']}\n"
                f"{'-' * 80}\n"
            )

        return "\n".join(formatted)

    def get_policy_by_exact_match(
        self,
        policy_type: str,
        section: str
    ) -> List[Dict[str, Any]]:
        """
        Get policies by exact metadata match.

        Args:
            policy_type: Exact policy type
            section: Exact section name

        Returns:
            All policies matching the criteria
        """
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"policy_type": {"$eq": policy_type}},
                        {"section": {"$eq": section}}
                    ]
                },
                include=["documents", "metadatas"]
            )

            formatted_results = []
            for i in range(len(results["documents"])):
                formatted_results.append({
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })

            logger.info(f"Found {len(formatted_results)} policies with exact match")
            return formatted_results

        except Exception as e:
            logger.error(f"Error in exact match retrieval: {e}")
            return []
