"""
Policy Parser Service

Parses uploaded policy documents (PDF, TXT, MD, DOCX) to extract:
- Metadata: title, version, policy_number, effective_date
- Sections: numbered sections with titles and content

Uses LLM-based structured extraction for improved accuracy.
"""

import re
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import concurrent.futures
from functools import wraps

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

from src.core.config import settings

logger = logging.getLogger(__name__)

try:
    from langchain_groq import ChatGroq
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import LangChain dependencies: {e}")
    LANGCHAIN_AVAILABLE = False


def timeout_handler(timeout_seconds=30):
    """Decorator to add timeout to function execution using threads."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    logger.error(f"Function {func.__name__} timed out after {timeout_seconds}s")
                    raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        return wrapper
    return decorator


@dataclass
class ParsedSection:
    """Represents a parsed policy section."""
    section_number: Optional[str]
    section_title: Optional[str]
    section_content: str
    section_order: int
    section_type: Optional[str] = None
    parent_section_id: Optional[str] = None


@dataclass
class ParsedPolicy:
    """Represents a parsed policy document."""
    title: str
    version: str
    policy_number: Optional[str]
    effective_date: Optional[str]
    full_text: str
    sections: List[ParsedSection]
    parsing_status: str  # 'success', 'partial', 'failed'
    parsing_errors: List[str]


class PolicyParserService:
    """Service for parsing policy documents using LLM-based extraction."""

    def __init__(self):
        """Initialize the parser with LangChain and Groq API."""
        if LANGCHAIN_AVAILABLE:
            try:
                self.llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=0.1,
                    groq_api_key=settings.groq_api_key,
                    timeout=30,  # 30 second timeout
                    max_retries=2,
                    model_kwargs={"response_format": {"type": "json_object"}}  # Enable JSON mode
                )
                self.use_llm = True
                logger.info("LangChain-based Groq LLM parser initialized successfully with Llama 3.3")
            except Exception as e:
                logger.error(f"Failed to initialize LangChain Groq LLM: {e}")
                self.use_llm = False
        else:
            logger.warning("LangChain not available. Using regex-based parsing.")
            self.use_llm = False

    def parse_document(self, file_path: str, file_type: str) -> ParsedPolicy:
        """
        Parse a policy document and extract structured data.

        Args:
            file_path: Path to the policy file
            file_type: File extension ('pdf', 'txt', 'md', 'docx')

        Returns:
            ParsedPolicy object with extracted data
        """
        parsing_errors = []

        try:
            # Extract raw text
            if file_type == 'pdf':
                text = self._extract_pdf_text(file_path)
            elif file_type == 'docx':
                text = self._extract_docx_text(file_path)
            else:
                text = self._read_text_file(file_path)

            if not text or len(text.strip()) == 0:
                return self._create_fallback_policy(file_path, "Empty document or text extraction failed")

            # Use LLM-based extraction if available, otherwise fallback to regex
            # Limit LLM usage to smaller documents to avoid timeouts
            if self.use_llm and len(text) < 100000:  # Reduced limit for better performance
                try:
                    logger.info(f"Attempting LLM parsing for document of length {len(text)}")
                    return self._llm_parse_document(text, file_path)
                except Exception as e:
                    logger.warning(f"LLM parsing failed, falling back to regex: {e}")
                    parsing_errors.append(f"LLM parsing failed: {str(e)}")
            elif self.use_llm:
                logger.info(f"Document too large ({len(text)} chars) for LLM, using regex")
                parsing_errors.append("Document too large for LLM parsing, using regex")

            # Fallback to regex-based parsing
            metadata = self._extract_metadata(text)
            sections = self._extract_sections(text)

            parsing_status = 'success'
            if not sections or len(sections) == 0:
                parsing_status = 'partial'
                parsing_errors.append("No structured sections found - created single section with full content")
                sections = [ParsedSection(
                    section_number=None,
                    section_title="Full Policy Content",
                    section_content=text[:50000],  # Limit content size
                    section_order=0
                )]

            return ParsedPolicy(
                title=metadata.get('title', self._extract_title_from_filename(file_path)),
                version=metadata.get('version', '1.0'),
                policy_number=metadata.get('policy_number'),
                effective_date=metadata.get('effective_date'),
                full_text=text,
                sections=sections,
                parsing_status=parsing_status,
                parsing_errors=parsing_errors
            )

        except Exception as e:
            logger.error(f"Error parsing policy {file_path}: {e}")
            return self._create_fallback_policy(file_path, str(e))

    def _llm_parse_document(self, text: str, file_path: str) -> ParsedPolicy:
        """
        Use LangChain with LLM to parse document with structured output.

        Args:
            text: Document text content
            file_path: Path to file for fallback title extraction

        Returns:
            ParsedPolicy with LLM-extracted data
        """
        logger.info(f"Starting LangChain Groq LLM-based parsing for {file_path}")

        # Limit text size for LLM to avoid timeouts
        max_text_length = 50000  # Reduced for faster processing
        text_sample = text[:max_text_length]

        # Create structured prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a legal document parser. Extract structured information from policy documents.

IMPORTANT INSTRUCTIONS:
1. Extract the policy title, version, policy number, and effective date from the document
2. Identify ALL sections, subsections, articles, and clauses in the document
3. For each section, extract:
   - Section number (e.g., "1", "1.1", "Article I", etc.)
   - Section title/heading
   - Section content (the actual text of that section, NOT including subsections)
4. Maintain hierarchical structure - if section 1.1 is under section 1, note that
5. DO NOT include empty sections - every section must have meaningful content
6. Preserve the original section numbering exactly as it appears
7. For sections without explicit numbers, assign logical sequential numbers

Return ONLY a valid JSON object with this exact structure:
{{
  "title": "Policy title from document or first heading",
  "version": "Version number if found, otherwise '1.0'",
  "policy_number": "Policy number if found, otherwise null",
  "effective_date": "Effective date if found in format YYYY-MM-DD, otherwise null",
  "sections": [
    {{
      "section_number": "Section number or identifier",
      "section_title": "Section heading or title",
      "section_content": "Complete text content of this section only",
      "section_type": "section|subsection|article|clause|appendix",
      "parent_section": "Parent section number if this is a subsection, otherwise null"
    }}
  ]
}}"""),
            ("user", "DOCUMENT TEXT:\n{text}")
        ])

        # Create JSON output parser
        json_parser = JsonOutputParser()

        # Create chain
        chain = prompt_template | self.llm | json_parser

        try:
            logger.info("Sending request to Groq API via LangChain (Llama 3.3)...")
            # Invoke chain with timeout handled by LangChain
            result = chain.invoke({"text": text_sample})
            logger.info("Received and parsed response from Groq API")

            # Validate response structure (result is already a dict from JsonOutputParser)
            if not isinstance(result, dict) or 'sections' not in result:
                raise ValueError("Invalid LLM response structure")

            # Convert to ParsedPolicy format
            sections = []
            for idx, section_data in enumerate(result.get('sections', [])):
                # Skip sections with empty or trivial content
                # Handle None values from JSON
                content = section_data.get('section_content') or ''
                if isinstance(content, str):
                    content = content.strip()
                else:
                    content = str(content).strip() if content else ''

                if not content or len(content) < 10:
                    continue

                sections.append(ParsedSection(
                    section_number=section_data.get('section_number'),
                    section_title=section_data.get('section_title'),
                    section_content=content,
                    section_order=idx,
                    section_type=section_data.get('section_type'),
                    parent_section_id=section_data.get('parent_section')
                ))

            # Extract metadata with fallbacks
            title = result.get('title') or ''
            if isinstance(title, str):
                title = title.strip()
            if not title:
                title = self._extract_title_from_filename(file_path)

            version = result.get('version') or '1.0'
            if not version or version == 'null' or version == 'None':
                version = '1.0'

            policy_number = result.get('policy_number')
            if policy_number in ('null', 'None', None):
                policy_number = None

            effective_date = result.get('effective_date')
            if effective_date in ('null', 'None', None):
                effective_date = None

            parsing_status = 'success' if sections else 'partial'
            parsing_errors = [] if sections else ["LLM found no valid sections"]

            # If no sections found, create fallback
            if not sections:
                sections = [ParsedSection(
                    section_number=None,
                    section_title="Full Policy Content",
                    section_content=text[:50000],
                    section_order=0
                )]

            return ParsedPolicy(
                title=title,
                version=version,
                policy_number=policy_number,
                effective_date=effective_date,
                full_text=text,
                sections=sections,
                parsing_status=parsing_status,
                parsing_errors=parsing_errors
            )

        except ValueError as e:
            logger.error(f"Invalid LLM response structure: {e}")
            raise
        except Exception as e:
            logger.error(f"LangChain LLM parsing error: {type(e).__name__}: {e}", exc_info=True)
            raise

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")

        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        if docx is None:
            raise ImportError("python-docx is required for DOCX parsing. Install with: pip install python-docx")

        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return ""

    def _read_text_file(self, file_path: str) -> str:
        """Read text from TXT or MD file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading text file: {e}")
                return ""

    def _extract_metadata(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract metadata from policy text using regex patterns.

        Looks for patterns like:
        - Title: <title>
        - Version: 2.1
        - Policy Number: FIN-001
        - Effective Date: 01/15/2024
        """
        metadata = {}

        # Extract title (look for "Title:" or use first non-empty line)
        title_match = re.search(r'^Title:\s*(.+)$', text, re.MULTILINE | re.IGNORECASE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        else:
            # Use first significant line (more than 5 chars)
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 5 and not line.startswith('#'):
                    metadata['title'] = line[:500]  # Limit title length
                    break

        # Extract version - improved patterns
        version_patterns = [
            r'version[:\s]+v?(\d+\.\d+(?:\.\d+)?)',
            r'v(\d+\.\d+(?:\.\d+)?)',
            r'rev(?:ision)?[:\s]+(\d+\.\d+)',
        ]
        for pattern in version_patterns:
            version_match = re.search(pattern, text, re.IGNORECASE)
            if version_match:
                metadata['version'] = version_match.group(1)
                break

        # Extract policy number - improved patterns
        policy_patterns = [
            r'policy\s+(?:number|no\.?|#|id)[:\s]+([A-Z0-9-]+)',
            r'document\s+(?:number|no\.?|id)[:\s]+([A-Z0-9-]+)',
            r'reference\s+(?:number|no\.?)[:\s]+([A-Z0-9-]+)',
        ]
        for pattern in policy_patterns:
            policy_num_match = re.search(pattern, text, re.IGNORECASE)
            if policy_num_match:
                metadata['policy_number'] = policy_num_match.group(1)
                break

        # Extract effective date - improved patterns
        date_patterns = [
            r'effective\s+(?:date|from)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'effective[:\s]+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                metadata['effective_date'] = date_match.group(1)
                break

        return metadata

    def _extract_sections(self, text: str) -> List[ParsedSection]:
        """
        Extract numbered sections from policy text using regex.

        Recognizes patterns like:
        - 1. Introduction
        - Section 1: Title
        - 1.1 Subsection
        - Article I - Title
        - ARTICLE 1 - Title
        """
        sections = []

        # Enhanced pattern to match various section formats
        section_patterns = [
            # Numbered sections: "1.", "1.1", "Section 1:", "1.1.1"
            r'^(?:Section\s+)?(\d+(?:\.\d+)*)[.:\s]+(.+?)$',
            # Article with Roman numerals: "Article I", "ARTICLE I -"
            r'^(?:Article\s+)?([IVX]+)[.\s-]+(.+?)$',
            # Article with numbers: "Article 1", "ARTICLE 1 -"
            r'^ARTICLE\s+(\d+)[.\s-]+(.+?)$',
            # Clause patterns: "Clause 1.1"
            r'^Clause\s+(\d+(?:\.\d+)*)[.:\s]+(.+?)$',
            # Lettered sections: "A.", "(a)"
            r'^(\(?[A-Z]\)?)[.:\s]+(.+?)$',
        ]

        lines = text.split('\n')
        current_section = None
        section_order = 0

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                if current_section:
                    current_section['content'] += '\n'
                continue

            # Try to match section patterns
            matched = False
            for pattern in section_patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    # Save previous section if it has content
                    if current_section and current_section['content'].strip():
                        sections.append(ParsedSection(
                            section_number=current_section['number'],
                            section_title=current_section['title'],
                            section_content=current_section['content'].strip(),
                            section_order=current_section['order']
                        ))

                    # Start new section
                    section_number = match.group(1)
                    section_title = match.group(2).strip()

                    current_section = {
                        'number': section_number,
                        'title': section_title,
                        'content': '',
                        'order': section_order
                    }
                    section_order += 1
                    matched = True
                    break

            # If not a section header, add to current section content
            if not matched and current_section:
                current_section['content'] += line + '\n'

        # Add last section (only if it has content)
        if current_section and current_section['content'].strip():
            sections.append(ParsedSection(
                section_number=current_section['number'],
                section_title=current_section['title'],
                section_content=current_section['content'].strip(),
                section_order=current_section['order']
            ))

        # Filter out sections with empty or trivial content
        sections = [s for s in sections if s.section_content and len(s.section_content.strip()) > 10]

        return sections

    def _extract_title_from_filename(self, file_path: str) -> str:
        """Extract title from filename as fallback."""
        filename = Path(file_path).stem  # Get filename without extension
        # Remove UUID prefixes if present
        filename = re.sub(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}_', '', filename)
        # Replace underscores and hyphens with spaces
        title = filename.replace('_', ' ').replace('-', ' ')
        # Capitalize words
        title = ' '.join(word.capitalize() for word in title.split())
        return title[:500]  # Limit length

    def _create_fallback_policy(self, file_path: str, error_message: str) -> ParsedPolicy:
        """Create a minimal policy when parsing fails."""
        logger.warning(f"Creating fallback policy for {file_path}: {error_message}")

        return ParsedPolicy(
            title=self._extract_title_from_filename(file_path),
            version='1.0',
            policy_number=None,
            effective_date=None,
            full_text='',
            sections=[],
            parsing_status='failed',
            parsing_errors=[error_message]
        )
