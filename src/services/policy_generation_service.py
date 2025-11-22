"""Service for AI-powered policy generation using Gemini LLM."""

import json
import re
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from src.core.config import settings
from src.core.constants import get_policy_type_by_id, PolicyType
import logging

logger = logging.getLogger(__name__)

# Configure Gemini
if settings.google_api_key:
    genai.configure(api_key=settings.google_api_key)


class Question:
    """Question model for policy questionnaire."""

    def __init__(
        self,
        id: str,
        text: str,
        type: str = "text",
        options: Optional[List[str]] = None,
        required: bool = True,
        help_text: Optional[str] = None,
        placeholder: Optional[str] = None
    ):
        self.id = id
        self.text = text
        self.type = type  # 'text', 'select', 'multiselect', 'number', 'date'
        self.options = options or []
        self.required = required
        self.help_text = help_text
        self.placeholder = placeholder

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "text": self.text,
            "type": self.type,
            "options": self.options,
            "required": self.required,
            "help_text": self.help_text,
            "placeholder": self.placeholder
        }


class PolicyGenerationService:
    """Service for generating policy questions and drafting policies using LLM."""

    def __init__(self):
        """Initialize the policy generation service."""
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.3,  # Slightly higher than analysis for creativity
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )

    def generate_questions(
        self,
        policy_type_id: str,
        company_context: Optional[Dict[str, Any]] = None
    ) -> List[Question]:
        """
        Generate contextual questions for a policy type using LLM.

        Args:
            policy_type_id: ID of the policy type
            company_context: Optional company information (name, industry, etc.)

        Returns:
            List of Question objects
        """
        try:
            # Get policy type metadata
            policy_type = get_policy_type_by_id(policy_type_id)
            if not policy_type:
                raise ValueError(f"Invalid policy type: {policy_type_id}")

            # Build context string
            context = ""
            if company_context:
                company_name = company_context.get("company_name", "the company")
                industry = company_context.get("industry", "")
                context = f"\nCompany: {company_name}"
                if industry:
                    context += f"\nIndustry: {industry}"

            # Construct prompt
            prompt = self._build_question_generation_prompt(policy_type, context)

            # Call LLM
            logger.info(f"Generating questions for policy type: {policy_type_id}")
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Parse JSON response
            questions = self._parse_questions_response(response_text)

            # Validate and fallback if needed
            if not questions or len(questions) < 5:
                logger.warning(f"LLM returned insufficient questions ({len(questions)}), using fallback")
                return self._get_fallback_questions(policy_type)

            logger.info(f"Successfully generated {len(questions)} questions")
            return questions

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            # Return fallback questions
            policy_type = get_policy_type_by_id(policy_type_id)
            if policy_type:
                return self._get_fallback_questions(policy_type)
            raise

    def _build_question_generation_prompt(self, policy_type: PolicyType, context: str) -> str:
        """Build the LLM prompt for question generation."""
        return f"""You are a legal policy expert helping to draft comprehensive {policy_type.name} policies.

Your task is to generate 8-12 targeted questions that will gather all necessary information to draft a professional {policy_type.name}.

Policy Type: {policy_type.name}
Description: {policy_type.description}
Category: {policy_type.category}{context}

Generate questions that cover:
1. Core requirements and scope
2. Key stakeholders and parties involved
3. Specific terms, conditions, and obligations
4. Compliance and legal requirements
5. Duration, renewal, and termination conditions
6. Special circumstances or exceptions
7. Enforcement and remedies

Return ONLY a JSON array of questions in this exact format (no markdown, no code blocks):
[
  {{
    "id": "q1",
    "text": "What is the primary purpose of this policy?",
    "type": "text",
    "required": true,
    "help_text": "Describe the main objective in 1-2 sentences",
    "placeholder": "e.g., To protect confidential business information..."
  }},
  {{
    "id": "q2",
    "text": "Who is covered by this policy?",
    "type": "select",
    "options": ["All employees", "Specific departments", "Contractors and vendors", "All parties"],
    "required": true,
    "help_text": "Select the scope of application"
  }}
]

Make questions:
- Specific to {policy_type.name}
- Clear and easy to understand
- Focused on gathering actionable information
- Progressive (building on each other logically)
- Use appropriate question types: text, select, multiselect, number, date

Generate between 8-12 questions. Return ONLY the JSON array, nothing else."""

    def _parse_questions_response(self, response_text: str) -> List[Question]:
        """Parse LLM response into Question objects."""
        try:
            # Remove markdown code blocks if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            response_text = response_text.strip()

            # Parse JSON
            questions_data = json.loads(response_text)

            # Validate it's a list
            if not isinstance(questions_data, list):
                logger.error("LLM response is not a JSON array")
                return []

            # Convert to Question objects
            questions = []
            for i, q_data in enumerate(questions_data):
                try:
                    question = Question(
                        id=q_data.get("id", f"q{i+1}"),
                        text=q_data.get("text", ""),
                        type=q_data.get("type", "text"),
                        options=q_data.get("options"),
                        required=q_data.get("required", True),
                        help_text=q_data.get("help_text"),
                        placeholder=q_data.get("placeholder")
                    )
                    if question.text:  # Only add if has text
                        questions.append(question)
                except Exception as e:
                    logger.warning(f"Skipping invalid question: {e}")
                    continue

            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            return []

    def _get_fallback_questions(self, policy_type: PolicyType) -> List[Question]:
        """Return generic fallback questions if LLM fails."""
        return [
            Question(
                id="q1",
                text=f"What is the primary purpose of this {policy_type.name}?",
                type="text",
                required=True,
                help_text="Describe the main objective in 1-2 sentences",
                placeholder="e.g., To establish guidelines for..."
            ),
            Question(
                id="q2",
                text="Who is covered by this policy?",
                type="select",
                options=["All employees", "Specific departments", "Contractors and vendors", "All parties"],
                required=True,
                help_text="Select the scope of application"
            ),
            Question(
                id="q3",
                text="What are the key requirements or obligations?",
                type="text",
                required=True,
                help_text="List the main requirements (3-5 bullet points)",
                placeholder="•  Requirement 1\n•  Requirement 2\n•  Requirement 3"
            ),
            Question(
                id="q4",
                text="What are the prohibited activities or violations?",
                type="text",
                required=False,
                help_text="Describe activities that are not allowed",
                placeholder="•  Prohibited action 1\n•  Prohibited action 2"
            ),
            Question(
                id="q5",
                text="How long is this policy effective?",
                type="select",
                options=["Indefinite", "1 year", "2 years", "3 years", "5 years", "Other"],
                required=True
            ),
            Question(
                id="q6",
                text="Who is responsible for enforcing this policy?",
                type="text",
                required=True,
                placeholder="e.g., HR Department, Compliance Officer, Management"
            ),
            Question(
                id="q7",
                text="What are the consequences of non-compliance?",
                type="text",
                required=True,
                help_text="Describe penalties or disciplinary actions",
                placeholder="e.g., Written warning, suspension, termination"
            ),
            Question(
                id="q8",
                text="Are there any exceptions or special circumstances?",
                type="text",
                required=False,
                help_text="Describe any situations where the policy doesn't apply",
                placeholder="e.g., Emergency situations, senior management approval"
            )
        ]

    def generate_policy(
        self,
        policy_type_id: str,
        answers: List[Dict[str, Any]],
        additional_notes: Optional[str] = None,
        company_name: str = "Company"
    ) -> Dict[str, Any]:
        """
        Generate a complete policy document based on answers.

        Args:
            policy_type_id: ID of the policy type
            answers: List of Q&A pairs [{"question_id": "...", "question_text": "...", "value": "..."}]
            additional_notes: Optional additional context from user
            company_name: Name of the company

        Returns:
            Dictionary with: title, content, sections, metadata
        """
        try:
            # Get policy type metadata
            policy_type = get_policy_type_by_id(policy_type_id)
            if not policy_type:
                raise ValueError(f"Invalid policy type: {policy_type_id}")

            # Build prompt
            prompt = self._build_policy_generation_prompt(
                policy_type, answers, additional_notes, company_name
            )

            # Call LLM
            logger.info(f"Generating policy for type: {policy_type_id}")
            response = self.model.generate_content(prompt)
            policy_content = response.text.strip()

            # Validate policy
            is_valid, validation_message = self._validate_policy(policy_content)
            if not is_valid:
                logger.warning(f"Generated policy failed validation: {validation_message}")
                # Retry once with enhanced prompt
                retry_prompt = f"{prompt}\n\nIMPORTANT: The policy must be well-structured with clear sections, proper numbering, and at least 500 characters. {validation_message}"
                response = self.model.generate_content(retry_prompt)
                policy_content = response.text.strip()

                # Validate again
                is_valid, validation_message = self._validate_policy(policy_content)
                if not is_valid:
                    raise ValueError(f"Failed to generate valid policy: {validation_message}")

            # Parse into sections
            sections = self._parse_policy_sections(policy_content)

            # Extract metadata
            metadata = {
                "policy_type": policy_type_id,
                "ai_generated": True,
                "generation_method": "llm_questionnaire",
                "question_count": len(answers),
                "has_additional_notes": bool(additional_notes)
            }

            # Extract title
            title = self._extract_title(policy_content, policy_type.name)

            logger.info(f"Successfully generated policy with {len(sections)} sections")

            return {
                "title": title,
                "content": policy_content,
                "sections": sections,
                "metadata": metadata,
                "version": "1.0"
            }

        except Exception as e:
            logger.error(f"Error generating policy: {str(e)}")
            raise

    def _build_policy_generation_prompt(
        self,
        policy_type: PolicyType,
        answers: List[Dict[str, Any]],
        additional_notes: Optional[str],
        company_name: str
    ) -> str:
        """Build the LLM prompt for policy generation."""
        # Format Q&A pairs
        qa_text = "\n".join([
            f"Q{i+1}: {answer['question_text']}\nA: {answer['value']}\n"
            for i, answer in enumerate(answers)
        ])

        notes_section = f"\nAdditional Context:\n{additional_notes}" if additional_notes else ""

        return f"""You are an expert legal policy writer. Draft a comprehensive, professional {policy_type.name} based on the following information.

Policy Type: {policy_type.name}
Company: {company_name}

Questions and Answers:
{qa_text}{notes_section}

Generate a complete, well-structured policy document that includes:

1. **Header Section**:
   - Policy Title (clear, professional)
   - Policy Number/Version: 1.0
   - Effective Date: [To be determined]
   - Review Date: [Annual review recommended]

2. **1.0 Purpose & Scope**:
   - Clear statement of purpose
   - Scope of application
   - Who is covered

3. **2.0 Definitions** (if needed):
   - Key terms used in the policy

4. **3.0 Policy Statements**:
   - Core requirements and rules
   - Obligations and responsibilities
   - Prohibited actions (if applicable)

5. **4.0 Procedures** (if applicable):
   - Step-by-step processes
   - Workflows and approvals

6. **5.0 Compliance & Enforcement**:
   - Monitoring and audit procedures
   - Consequences of non-compliance

7. **6.0 Related Documents**:
   - References to other policies
   - Legal/regulatory citations (if applicable)

8. **7.0 Approval & Review**:
   - Approval authority
   - Review frequency

Format requirements:
- Use clear, professional legal language
- Include section numbers (1.0, 1.1, 2.0, etc.)
- Use bullet points and numbered lists where appropriate
- Keep sentences concise and unambiguous
- Follow standard legal document structure
- Minimum 800 words for comprehensive coverage

Return the complete policy document in markdown format with proper headings (# for title, ## for main sections, ### for subsections).

Policy Document:"""

    def _validate_policy(self, policy_content: str) -> tuple[bool, str]:
        """Validate that generated policy meets quality standards."""
        checks = {
            "has_title": bool(re.search(r'^#\s+.+', policy_content, re.MULTILINE)),
            "has_sections": len(re.findall(r'^##\s+', policy_content, re.MULTILINE)) >= 3,
            "has_numbering": bool(re.search(r'\d+\.\d+', policy_content)),
            "min_length": len(policy_content) >= 500,
            "max_length": len(policy_content) <= 50000,
            "has_purpose": "purpose" in policy_content.lower() or "scope" in policy_content.lower(),
        }

        failed_checks = [k for k, v in checks.items() if not v]

        if failed_checks:
            return False, f"Failed validation checks: {', '.join(failed_checks)}"

        return True, "Validation passed"

    def _parse_policy_sections(self, policy_content: str) -> List[Dict[str, str]]:
        """Parse markdown policy into structured sections."""
        sections = []

        # Split by ## headings (main sections)
        section_pattern = r'##\s+([\d\.]+)?\s*(.+?)(?=\n##|\Z)'
        matches = re.finditer(section_pattern, policy_content, re.DOTALL)

        for match in matches:
            section_number = match.group(1) or ""
            section_title = match.group(2).strip()
            section_content = match.group(0).strip()

            sections.append({
                "section_number": section_number.strip(),
                "section_title": section_title,
                "section_content": section_content
            })

        return sections

    def _extract_title(self, policy_content: str, fallback_name: str) -> str:
        """Extract policy title from content."""
        # Look for # heading at start
        title_match = re.search(r'^#\s+(.+?)$', policy_content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        return fallback_name


# Global service instance
policy_generation_service = PolicyGenerationService()
