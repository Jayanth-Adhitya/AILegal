"""Policy document embeddings and ingestion."""

import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
import chromadb
from chromadb.config import Settings as ChromaSettings
import PyPDF2
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

try:
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    ResourceExhausted = Exception

from ..core.config import settings

logger = logging.getLogger(__name__)


class LocalEmbeddings:
    """
    Local embedding model wrapper using sentence-transformers.

    No API calls, no rate limits, completely free!
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize local embedding model.

        Args:
            model_name: HuggingFace model name
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        logger.info(f"Loading local embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"✅ Local model loaded successfully (dimension: {self.model.get_sentence_embedding_dimension()})")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            show_progress_bar=len(texts) > 10,
            convert_to_numpy=True
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()


class PolicyEmbeddings:
    """Handles policy document embedding generation and ChromaDB storage."""

    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize embeddings model and ChromaDB client.

        Args:
            collection_name: Optional collection name. If not provided, uses default from settings.
        """
        # Initialize embedding model (local or API-based)
        if settings.use_local_embeddings:
            logger.info("🖥️  Using LOCAL embedding model (no API limits!)")
            self.embeddings = LocalEmbeddings(settings.local_embedding_model)
            self.is_local = True
        else:
            logger.info("☁️  Using Gemini API embedding model")
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.embedding_model,
                google_api_key=settings.google_api_key
            )
            self.is_local = False

        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Store collection name for later use
        self.collection_name = collection_name or settings.chroma_collection_name

        # Initialize default collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        logger.info(f"Initialized PolicyEmbeddings with collection: {self.collection_name}")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((ResourceExhausted, Exception)),
        reraise=True
    )
    def _embed_with_retry(self, texts: List[str]) -> List[List[float]]:
        """
        Embed texts with automatic retry on rate limit errors.

        Uses exponential backoff: 4s, 8s, 16s, 32s, 60s between retries.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            ResourceExhausted: If rate limit persists after retries
        """
        try:
            return self.embeddings.embed_documents(texts)
        except ResourceExhausted as e:
            logger.warning(f"Rate limit hit, retrying... ({e})")
            raise
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    def embed_documents_batched(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        delay: Optional[float] = None,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Embed documents in batches with rate limiting protection.

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts per batch (default: from settings)
            delay: Delay in seconds between batches (default: from settings)
            show_progress: Whether to log progress

        Returns:
            List of embedding vectors
        """
        # Local embeddings don't need rate limiting - process all at once
        if self.is_local:
            logger.info(f"🖥️  Embedding {len(texts)} texts locally (no rate limits)...")
            return self.embeddings.embed_documents(texts)

        # API-based embeddings need batching and delays
        batch_size = batch_size or settings.embedding_batch_size
        delay = delay or settings.embedding_delay_seconds

        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        logger.info(
            f"☁️  Embedding {len(texts)} texts via API in {total_batches} batch(es) "
            f"(batch_size={batch_size}, delay={delay}s)"
        )

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1

            if show_progress:
                logger.info(
                    f"Processing batch {batch_num}/{total_batches} "
                    f"({len(batch)} texts)..."
                )

            try:
                # Embed batch with retry protection
                batch_embeddings = self._embed_with_retry(batch)
                all_embeddings.extend(batch_embeddings)

                # Add delay between batches (except for last batch)
                if i + batch_size < len(texts):
                    if show_progress:
                        logger.info(f"Waiting {delay}s before next batch...")
                    time.sleep(delay)

            except Exception as e:
                logger.error(
                    f"Failed to embed batch {batch_num}/{total_batches}: {e}"
                )
                raise

        logger.info(f"✅ Successfully embedded {len(all_embeddings)} texts")
        return all_embeddings

    def get_user_collection_name(self, company_id: str) -> str:
        """
        Generate collection name for a specific company.

        Args:
            company_id: The company's unique identifier

        Returns:
            Collection name in format: policies_{company_id}
        """
        return f"policies_{company_id}"

    def get_or_create_user_collection(self, company_id: Optional[str] = None):
        """
        Get or create a user-specific collection.

        Args:
            company_id: Company ID for user-specific collection. If None, uses default.

        Returns:
            ChromaDB collection instance
        """
        if company_id:
            collection_name = self.get_user_collection_name(company_id)
            logger.info(f"Using user-specific collection: {collection_name}")
        else:
            collection_name = self.collection_name
            logger.info(f"Using default collection: {collection_name}")

        collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "company_id": company_id if company_id else None
            }
        )

        return collection

    def load_policy_file(self, file_path: Path) -> str:
        """Load a policy file and return its content (supports .txt, .md, .pdf)."""
        try:
            # Handle PDF files
            if file_path.suffix.lower() == '.pdf':
                content = self._extract_text_from_pdf(file_path)
            else:
                # Handle text files (.txt, .md)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            logger.info(f"Loaded policy file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error loading policy file {file_path}: {e}")
            raise

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file."""
        try:
            text_content = []
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)

            content = "\n\n".join(text_content)
            logger.info(f"Extracted {len(pdf_reader.pages)} pages from PDF: {pdf_path}")
            return content

        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise

    def extract_metadata_from_filename(self, filename: str) -> Dict[str, str]:
        """Extract metadata from policy filename."""
        # Expected format: PolicyType_Section_Version.{txt|md|pdf}
        # Example: Legal_Liability_v1.0.txt, Commercial_PaymentTerms_v2.1.pdf
        # Remove file extension
        name_without_ext = filename.replace('.txt', '').replace('.md', '').replace('.pdf', '')
        parts = name_without_ext.split('_')

        metadata = {
            "filename": filename,
            "policy_type": parts[0] if len(parts) > 0 else "unknown",
            "section": parts[1] if len(parts) > 1 else "general",
            "version": parts[2] if len(parts) > 2 else "v1.0"
        }

        return metadata

    def chunk_document(self, content: str, metadata: Dict[str, str]) -> List[Document]:
        """Split document into chunks with metadata."""
        chunks = self.text_splitter.split_text(content)

        documents = [
            Document(
                page_content=chunk,
                metadata={
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            for i, chunk in enumerate(chunks)
        ]

        logger.info(f"Created {len(documents)} chunks from document")
        return documents

    def ingest_single_file(self, file_path: Path, company_id: Optional[str] = None) -> int:
        """
        Ingest a single policy file into user-specific or default collection.

        Args:
            file_path: Path to the policy file
            company_id: Optional company ID for user-specific collection

        Returns:
            Number of chunks ingested
        """
        try:
            # Get the appropriate collection
            collection = self.get_or_create_user_collection(company_id)

            # Load file content
            content = self.load_policy_file(file_path)

            # Extract metadata
            metadata = self.extract_metadata_from_filename(file_path.name)
            metadata["source_type"] = "policy"
            metadata["file_path"] = str(file_path)
            if company_id:
                metadata["company_id"] = company_id

            # Add upload timestamp
            from datetime import datetime
            metadata["uploaded_at"] = datetime.now().isoformat()

            # Chunk the document
            documents = self.chunk_document(content, metadata)

            # Generate embeddings (with rate limiting protection)
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            embeddings_list = self.embed_documents_batched(texts, show_progress=False)

            # Add to ChromaDB
            import uuid
            import time
            timestamp = int(time.time() * 1000)
            ids = [f"{file_path.stem}_{timestamp}_{i}" for i in range(len(documents))]

            collection.add(
                documents=texts,
                embeddings=embeddings_list,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Ingested {file_path.name}: {len(documents)} chunks to {collection.name}")
            return len(documents)

        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {e}")
            raise

    def ingest_policy_directory(self, directory: str, policy_type: str = "policy") -> int:
        """
        Ingest all policy files from a directory.

        Args:
            directory: Path to directory containing policy files
            policy_type: Type of policies ("policy" or "law")

        Returns:
            Number of chunks ingested
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return 0

        total_chunks = 0
        policy_files = (
            list(directory_path.glob("*.txt")) +
            list(directory_path.glob("*.md")) +
            list(directory_path.glob("*.pdf"))
        )

        logger.info(f"Found {len(policy_files)} policy files in {directory}")

        for policy_file in policy_files:
            try:
                # Load file content
                content = self.load_policy_file(policy_file)

                # Extract metadata
                metadata = self.extract_metadata_from_filename(policy_file.name)
                metadata["source_type"] = policy_type
                metadata["file_path"] = str(policy_file)

                # Chunk the document
                documents = self.chunk_document(content, metadata)

                # Generate embeddings (with rate limiting protection)
                texts = [doc.page_content for doc in documents]
                metadatas = [doc.metadata for doc in documents]

                embeddings_list = self.embed_documents_batched(texts, show_progress=True)

                # Add to ChromaDB
                ids = [f"{policy_file.stem}_{i}" for i in range(len(documents))]

                self.collection.add(
                    documents=texts,
                    embeddings=embeddings_list,
                    metadatas=metadatas,
                    ids=ids
                )

                total_chunks += len(documents)
                logger.info(f"Ingested {policy_file.name}: {len(documents)} chunks")

            except Exception as e:
                logger.error(f"Error ingesting {policy_file}: {e}")
                continue

        logger.info(f"Total chunks ingested: {total_chunks}")
        return total_chunks

    def ingest_policies(self) -> Dict[str, int]:
        """Ingest all policies and laws from data directories."""
        results = {
            "policies": self.ingest_policy_directory("data/policies", "policy"),
            "laws": self.ingest_policy_directory("data/laws", "law")
        }

        total = sum(results.values())
        logger.info(f"Total ingestion complete: {total} chunks ({results})")

        return results

    def ingest_regional_directory(
        self,
        region_code: str,
        directory_path: str
    ) -> int:
        """
        Ingest regional policy directory into region-specific collection.

        Creates a separate ChromaDB collection for the region and ingests all
        documents with regional metadata tagging.

        Args:
            region_code: Region identifier (e.g., "dubai_uae")
            directory_path: Path to directory containing regional documents

        Returns:
            Number of chunks ingested (0 if collection already populated or directory missing)

        Example:
            >>> embeddings = PolicyEmbeddings()
            >>> chunks = embeddings.ingest_regional_directory("dubai_uae", "data/regional/dubai_uae")
            >>> print(f"Ingested {chunks} chunks")
        """
        from ..core.config import REGION_CONFIG

        # Get regional collection name
        collection_name = f"policies_{region_code}"

        # Get or create regional collection
        try:
            regional_collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine", "region": region_code}
            )

            # Check idempotency - skip if already populated
            existing_count = regional_collection.count()
            if existing_count > 0:
                logger.info(f"Region {region_code} already ingested ({existing_count} docs)")
                return 0

        except Exception as e:
            logger.error(f"Failed to get/create collection for region {region_code}: {e}")
            return 0

        # Check if directory exists
        directory = Path(directory_path)
        if not directory.exists():
            logger.warning(f"Regional directory not found for {region_code}: {directory_path}")
            return 0

        # Get regional metadata from config
        region_metadata = REGION_CONFIG.get(region_code, {}).get("metadata", {})

        # Find all policy files
        policy_files = (
            list(directory.glob("*.txt")) +
            list(directory.glob("*.md")) +
            list(directory.glob("*.pdf"))
        )

        if not policy_files:
            logger.warning(f"No documents found in {directory_path}")
            return 0

        logger.info(f"Found {len(policy_files)} regional documents in {directory_path}")

        total_chunks = 0
        for policy_file in policy_files:
            try:
                # Load file content
                content = self.load_policy_file(policy_file)

                # Extract metadata from filename
                metadata = self.extract_metadata_from_filename(policy_file.name)

                # Add regional metadata
                metadata["source_type"] = "regional"
                metadata["region"] = region_code
                metadata["region_name"] = region_metadata.get("region_name", region_code)
                metadata["legal_jurisdiction"] = region_metadata.get("legal_jurisdiction", "")
                metadata["file_path"] = str(policy_file)

                # Add upload timestamp
                from datetime import datetime
                metadata["uploaded_at"] = datetime.now().isoformat()

                # Chunk the document
                documents = self.chunk_document(content, metadata)

                # Generate embeddings (with rate limiting protection)
                texts = [doc.page_content for doc in documents]
                metadatas = [doc.metadata for doc in documents]

                embeddings_list = self.embed_documents_batched(texts, show_progress=True)

                # Add to regional collection
                import time
                timestamp = int(time.time() * 1000)
                ids = [f"{policy_file.stem}_{region_code}_{timestamp}_{i}" for i in range(len(documents))]

                regional_collection.add(
                    documents=texts,
                    embeddings=embeddings_list,
                    metadatas=metadatas,
                    ids=ids
                )

                total_chunks += len(documents)
                logger.info(f"Ingested {policy_file.name}: {len(documents)} chunks")

            except Exception as e:
                logger.error(f"Error ingesting regional file {policy_file}: {e}")
                continue

        logger.info(f"Total chunks ingested for region {region_code}: {total_chunks}")
        return total_chunks

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        count = self.collection.count()

        return {
            "total_documents": count,
            "collection_name": settings.chroma_collection_name,
            "embedding_model": settings.embedding_model
        }

    def get_regional_collection_stats(self, region_code: str) -> Dict[str, Any]:
        """
        Get statistics for a regional collection.

        Args:
            region_code: Region identifier (e.g., "dubai_uae")

        Returns:
            Dictionary with collection statistics.
        """
        collection_name = f"policies_{region_code}"

        try:
            regional_collection = self.chroma_client.get_collection(name=collection_name)
            count = regional_collection.count()

            return {
                "total_documents": count,
                "collection_name": collection_name,
                "region_code": region_code,
                "embedding_model": settings.embedding_model
            }

        except Exception as e:
            logger.error(f"Failed to get stats for region {region_code}: {e}")
            return {
                "total_documents": 0,
                "collection_name": collection_name,
                "region_code": region_code,
                "error": str(e)
            }

    def get_all_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics for all collections (global + regional).

        Returns:
            Dictionary mapping collection names to document counts.
        """
        all_stats = {}

        # Get all collections
        try:
            collections = self.chroma_client.list_collections()
            for collection_info in collections:
                collection_name = collection_info.name
                collection = self.chroma_client.get_collection(name=collection_name)
                all_stats[collection_name] = collection.count()
        except Exception as e:
            logger.error(f"Failed to get all collection stats: {e}")

        return all_stats

    def clear_collection(self):
        """Clear all documents from the collection (use with caution)."""
        self.chroma_client.delete_collection(settings.chroma_collection_name)
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.warning("Collection cleared")

    def embed_policy_section(
        self,
        section_id: str,
        section_content: str,
        metadata: Dict[str, Any],
        company_id: str
    ):
        """
        Embed a single policy section into ChromaDB.

        Args:
            section_id: Unique section identifier
            section_content: Text content of the section
            metadata: Metadata including policy_id, section_number, etc.
            company_id: Company ID for multi-tenant isolation
        """
        try:
            # Get user's collection
            collection = self.get_or_create_user_collection(company_id)

            # Generate embedding
            embedding = self.embeddings.embed_query(section_content)

            # Add to ChromaDB with enhanced metadata
            collection.add(
                documents=[section_content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[section_id]
            )

            logger.info(f"Embedded section {section_id} for policy {metadata.get('policy_id')}")

        except Exception as e:
            logger.error(f"Error embedding section {section_id}: {e}")
            raise

    def delete_policy_embeddings(self, policy_id: str, company_id: str):
        """
        Delete all embeddings for a policy.

        Args:
            policy_id: Policy ID
            company_id: Company ID
        """
        try:
            collection = self.get_or_create_user_collection(company_id)

            # Query for all sections with this policy_id
            results = collection.get(
                where={"policy_id": policy_id},
                include=["metadatas"]
            )

            if results and results.get('ids'):
                ids_to_delete = results['ids']
                collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} embeddings for policy {policy_id}")
            else:
                logger.info(f"No embeddings found for policy {policy_id}")

        except Exception as e:
            logger.error(f"Error deleting embeddings for policy {policy_id}: {e}")
            raise
