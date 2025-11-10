"""Generate Word documents with track changes and comments."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_COLOR_INDEX

logger = logging.getLogger(__name__)


class DocxGenerator:
    """Generate Word documents with track changes and AI comments."""

    def __init__(self, original_doc_path: Optional[str] = None):
        """
        Initialize generator.

        Args:
            original_doc_path: Path to original document (to preserve formatting)
        """
        if original_doc_path:
            self.document = Document(original_doc_path)
            logger.info(f"Loaded original document: {Path(original_doc_path).name}")
        else:
            self.document = Document()
            logger.info("Created new blank document")

    def add_comment_to_paragraph(
        self,
        paragraph_index: int,
        comment_text: str,
        author: str = "AI Legal Assistant",
        initials: str = "AI"
    ) -> bool:
        """
        Add a comment to a specific paragraph.

        Args:
            paragraph_index: Index of the paragraph to comment on
            comment_text: The comment content
            author: Comment author name
            initials: Author initials

        Returns:
            True if comment added successfully
        """
        try:
            if paragraph_index >= len(self.document.paragraphs):
                logger.error(f"Paragraph index {paragraph_index} out of range")
                return False

            paragraph = self.document.paragraphs[paragraph_index]

            # Add comment to all runs in the paragraph
            if paragraph.runs:
                self.document.add_comment(
                    runs=paragraph.runs,
                    text=comment_text,
                    author=author,
                    initials=initials
                )
                logger.debug(f"Added comment to paragraph {paragraph_index}")
                return True
            else:
                logger.warning(f"Paragraph {paragraph_index} has no runs")
                return False

        except Exception as e:
            logger.error(f"Error adding comment to paragraph {paragraph_index}: {e}")
            return False

    def add_inline_comment(
        self,
        paragraph_index: int,
        comment_text: str,
        highlight_text: bool = True
    ) -> bool:
        """
        Add an inline visual comment (as highlighted text with note).

        Note: python-docx has limitations with Word's native commenting system.
        This method adds a visible indicator in the document.

        Args:
            paragraph_index: Index of the paragraph
            comment_text: The comment content
            highlight_text: Whether to highlight the commented text

        Returns:
            True if successful
        """
        try:
            if paragraph_index >= len(self.document.paragraphs):
                return False

            paragraph = self.document.paragraphs[paragraph_index]

            # Add a visual comment marker
            comment_run = paragraph.add_run(f" [AI COMMENT: {comment_text}]")
            comment_run.font.color.rgb = RGBColor(255, 0, 0)  # Red color
            comment_run.font.size = Pt(9)
            comment_run.font.italic = True

            # Highlight original text if requested
            if highlight_text and paragraph.runs:
                for run in paragraph.runs[:-1]:  # Exclude the comment run we just added
                    run.font.highlight_color = WD_COLOR_INDEX.YELLOW

            logger.debug(f"Added inline comment to paragraph {paragraph_index}")
            return True

        except Exception as e:
            logger.error(f"Error adding inline comment: {e}")
            return False

    def add_redline_suggestion(
        self,
        paragraph_index: int,
        original_text: str,
        suggested_text: str,
        explanation: str
    ) -> bool:
        """
        Add a redline suggestion by showing strikethrough and new text.

        Args:
            paragraph_index: Index of the paragraph
            original_text: Original clause text
            suggested_text: Suggested replacement text
            explanation: Explanation for the change

        Returns:
            True if successful
        """
        try:
            if paragraph_index >= len(self.document.paragraphs):
                return False

            paragraph = self.document.paragraphs[paragraph_index]

            # Clear existing runs
            for run in paragraph.runs:
                run.text = ""

            # Add strikethrough for original text
            deleted_run = paragraph.add_run(original_text)
            deleted_run.font.strike = True
            deleted_run.font.color.rgb = RGBColor(255, 0, 0)  # Red

            # Add space
            paragraph.add_run(" ")

            # Add suggested text
            suggested_run = paragraph.add_run(suggested_text)
            suggested_run.font.color.rgb = RGBColor(0, 128, 0)  # Green
            suggested_run.font.bold = True

            # Add explanation as comment
            self.add_inline_comment(paragraph_index, explanation, highlight_text=False)

            logger.debug(f"Added redline to paragraph {paragraph_index}")
            return True

        except Exception as e:
            logger.error(f"Error adding redline: {e}")
            return False

    def create_review_document(
        self,
        analysis_results: List[Dict[str, Any]],
        output_path: str
    ) -> bool:
        """
        Create a complete review document with all comments and redlines.

        Args:
            analysis_results: List of clause analysis results
            output_path: Path to save the output document

        Returns:
            True if document created successfully
        """
        try:
            for result in analysis_results:
                paragraph_index = result.get("paragraph_index")
                compliant = result.get("compliant", True)

                if not compliant:
                    # Add rejection comment
                    comment_text = self._format_rejection_comment(result)
                    self.add_inline_comment(paragraph_index, comment_text)

                    # If there's a redline suggestion, add it (support both field names)
                    suggested_text = result.get("suggested_alternative") or result.get("redline_suggestion")
                    if suggested_text:
                        self.add_redline_suggestion(
                            paragraph_index=paragraph_index,
                            original_text=result.get("text", ""),
                            suggested_text=suggested_text,
                            explanation=result.get("rejection_reason", "")
                        )

            # Save the document
            self.document.save(output_path)
            logger.info(f"Saved review document to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating review document: {e}")
            return False

    def _format_rejection_comment(self, result: Dict[str, Any]) -> str:
        """Format a rejection comment with policy citations."""
        comment_parts = [
            "REJECTED - Non-compliant clause",
            "",
            f"Reason: {result.get('rejection_reason', 'Policy violation')}",
        ]

        # Add policy citations (support both field names)
        policy_refs = result.get("policy_references") or result.get("policy_citations") or []
        if policy_refs:
            comment_parts.append("")
            comment_parts.append("Policy References:")
            for citation in policy_refs:
                comment_parts.append(f"  - {citation}")

        # Add risk level
        if result.get("risk_level"):
            comment_parts.append("")
            comment_parts.append(f"Risk Level: {result['risk_level'].upper()}")

        # Add suggested action (support both field names)
        suggested_text = result.get("suggested_alternative") or result.get("redline_suggestion")
        if suggested_text:
            comment_parts.append("")
            comment_parts.append("Suggested Alternative:")
            comment_parts.append(suggested_text)

        return "\n".join(comment_parts)

    def add_summary_page(
        self,
        summary: Dict[str, Any]
    ):
        """
        Add a summary page at the beginning of the document.

        Args:
            summary: Contract analysis summary
        """
        # Insert a new paragraph at the beginning
        intro_para = self.document.add_paragraph()
        self.document.paragraphs.insert(0, intro_para)

        # Add title
        title = self.document.add_paragraph("AI Legal Assistant - Contract Review Summary")
        title.style = "Heading 1"
        self.document.paragraphs.insert(0, title)

        # Add summary content
        summary_para = self.document.add_paragraph()
        summary_para.add_run("Contract Type: ").bold = True
        summary_para.add_run(f"{summary.get('contract_type', 'Unknown')}\n")

        summary_para.add_run("Total Clauses Reviewed: ").bold = True
        summary_para.add_run(f"{summary.get('total_clauses_reviewed', 0)}\n")

        summary_para.add_run("Compliant Clauses: ").bold = True
        summary_para.add_run(f"{summary.get('compliant_clauses', 0)}\n")

        summary_para.add_run("Non-Compliant Clauses: ").bold = True
        summary_para.add_run(f"{summary.get('non_compliant_clauses', 0)}\n")

        summary_para.add_run("Overall Risk: ").bold = True
        risk_run = summary_para.add_run(f"{summary.get('overall_risk_assessment', 'Unknown').upper()}\n")

        # Color code risk
        risk_colors = {
            "low": RGBColor(0, 128, 0),
            "medium": RGBColor(255, 165, 0),
            "high": RGBColor(255, 0, 0),
            "critical": RGBColor(139, 0, 0)
        }
        risk_level = summary.get('overall_risk_assessment', '').lower()
        if risk_level in risk_colors:
            risk_run.font.color.rgb = risk_colors[risk_level]

        # Add page break
        self.document.add_page_break()

        logger.info("Added summary page to document")

    def save(self, output_path: str):
        """Save the document to a file."""
        self.document.save(output_path)
        logger.info(f"Document saved to: {output_path}")
