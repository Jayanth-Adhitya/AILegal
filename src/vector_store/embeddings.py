"""Policy document embeddings and ingestion."""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
import chromadb
from chromadb.config import Settings as ChromaSettings
import PyPDF2

from ..core.config import settings

logger = logging.getLogger(__name__)


class PolicyEmbeddings:
    """Handles policy document embedding generation and ChromaDB storage."""

    def __init__(self):
        """Initialize embeddings model and ChromaDB client."""
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key
        )

        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        logger.info(f"Initialized PolicyEmbeddings with collection: {settings.chroma_collection_name}")

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

                # Generate embeddings
                texts = [doc.page_content for doc in documents]
                metadatas = [doc.metadata for doc in documents]

                embeddings_list = self.embeddings.embed_documents(texts)

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

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        count = self.collection.count()

        return {
            "total_documents": count,
            "collection_name": settings.chroma_collection_name,
            "embedding_model": settings.embedding_model
        }

    def clear_collection(self):
        """Clear all documents from the collection (use with caution)."""
        self.chroma_client.delete_collection(settings.chroma_collection_name)
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.warning("Collection cleared")
