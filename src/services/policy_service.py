"""
Policy Service

Business logic for policy management including:
- Creating policies with sections
- Updating policies and tracking versions
- Deleting policies and cleaning up vector store
- Validating policy data
"""

import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.models import Policy, PolicySection, PolicyVersion, User as DBUser
from src.services.policy_parser import PolicyParserService, ParsedPolicy

logger = logging.getLogger(__name__)


class PolicyService:
    """Service for policy business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.parser = PolicyParserService()

    def create_policy(
        self,
        policy_id: str,
        company_id: str,
        created_by_user_id: str,
        title: str,
        policy_number: Optional[str],
        version: str,
        effective_date: Optional[datetime],
        original_filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        full_text: str,
        parsed_data: ParsedPolicy,
        metadata: Optional[Dict] = None
    ) -> Policy:
        """
        Create a policy from already-parsed data.

        Args:
            policy_id: Unique ID for the policy
            company_id: Company ID for multi-tenant isolation
            created_by_user_id: User ID who created the policy
            title: Policy title
            policy_number: Policy number (optional)
            version: Policy version
            effective_date: Effective date (optional)
            original_filename: Original filename
            file_path: Path to policy file
            file_size: File size in bytes
            file_type: File extension ('pdf', 'txt', 'md')
            full_text: Full text content
            parsed_data: ParsedPolicy object with sections
            metadata: Additional metadata (optional)

        Returns:
            Created Policy object with sections
        """
        # Create policy record
        policy = Policy(
            id=policy_id,
            company_id=company_id,
            created_by_user_id=created_by_user_id,
            title=title,
            policy_number=policy_number,
            version=version,
            effective_date=effective_date,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            full_text=full_text,
            status='draft' if parsed_data.parsing_status == 'failed' else 'active',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.db.add(policy)

        # Create section records
        for parsed_section in parsed_data.sections:
            section_id = str(uuid.uuid4())
            section = PolicySection(
                id=section_id,
                policy_id=policy_id,
                section_number=parsed_section.section_number,
                section_title=parsed_section.section_title,
                section_content=parsed_section.section_content,
                section_order=parsed_section.section_order,
                section_type=parsed_section.section_type,
                parent_section_id=parsed_section.parent_section_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.db.add(section)

        self.db.commit()
        self.db.refresh(policy)

        logger.info(f"Created policy {policy_id} with {len(parsed_data.sections)} sections (status: {parsed_data.parsing_status})")
        return policy

    def create_policy_from_upload(
        self,
        file_path: str,
        original_filename: str,
        file_size: int,
        file_type: str,
        company_id: str,
        user_id: str
    ) -> Policy:
        """
        Create a policy from an uploaded file.

        Args:
            file_path: Path to uploaded file
            original_filename: Original filename
            file_size: File size in bytes
            file_type: File extension ('pdf', 'txt', 'md')
            company_id: Company ID for multi-tenant isolation
            user_id: User ID who uploaded the policy

        Returns:
            Created Policy object with sections
        """
        # Parse the document
        parsed = self.parser.parse_document(file_path, file_type)

        # Create policy record
        policy_id = str(uuid.uuid4())
        policy = Policy(
            id=policy_id,
            company_id=company_id,
            created_by_user_id=user_id,
            title=parsed.title,
            policy_number=parsed.policy_number,
            version=parsed.version,
            effective_date=self._parse_date(parsed.effective_date) if parsed.effective_date else None,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            full_text=parsed.full_text,
            status='draft' if parsed.parsing_status == 'failed' else 'active',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.db.add(policy)

        # Create section records
        for parsed_section in parsed.sections:
            section_id = str(uuid.uuid4())
            section = PolicySection(
                id=section_id,
                policy_id=policy_id,
                section_number=parsed_section.section_number,
                section_title=parsed_section.section_title,
                section_content=parsed_section.section_content,
                section_order=parsed_section.section_order,
                section_type=parsed_section.section_type,
                parent_section_id=parsed_section.parent_section_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.db.add(section)

        self.db.commit()
        self.db.refresh(policy)

        logger.info(f"Created policy {policy_id} with {len(parsed.sections)} sections (status: {parsed.parsing_status})")
        return policy

    def get_policy(self, policy_id: str, company_id: str) -> Optional[Policy]:
        """Get policy by ID, ensuring company_id matches."""
        return self.db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.company_id == company_id
        ).first()

    def list_policies(
        self,
        company_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Policy]:
        """
        List policies for a company with optional filtering.

        Args:
            company_id: Company ID
            status: Optional status filter ('active', 'archived', 'draft')
            search: Optional search query (searches title, policy_number)
            limit: Max number of results
            offset: Offset for pagination

        Returns:
            List of Policy objects
        """
        query = self.db.query(Policy).filter(Policy.company_id == company_id)

        if status:
            query = query.filter(Policy.status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Policy.title.ilike(search_pattern)) |
                (Policy.policy_number.ilike(search_pattern))
            )

        query = query.order_by(Policy.created_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    def update_policy(
        self,
        policy_id: str,
        company_id: str,
        user_id: str,
        update_data: Dict,
        change_description: Optional[str] = None
    ) -> Policy:
        """
        Update a policy and create version snapshot.

        Args:
            policy_id: Policy ID to update
            company_id: Company ID for security
            user_id: User making the change
            update_data: Dictionary with fields to update
            change_description: Description of changes

        Returns:
            Updated Policy object

        Raises:
            ValueError: If policy not found or validation fails
        """
        policy = self.get_policy(policy_id, company_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")

        # Validate updates
        self._validate_policy_update(policy, update_data, company_id)

        # Create version snapshot before updating
        self._create_version_snapshot(policy, user_id, change_description)

        # Update policy fields
        if 'title' in update_data:
            policy.title = update_data['title']
        if 'policy_number' in update_data:
            policy.policy_number = update_data['policy_number']
        if 'version' in update_data:
            policy.version = update_data['version']
        if 'effective_date' in update_data:
            policy.effective_date = self._parse_date(update_data['effective_date'])
        if 'full_text' in update_data:
            policy.full_text = update_data['full_text']
        if 'summary' in update_data:
            policy.summary = update_data['summary']
        if 'status' in update_data:
            policy.status = update_data['status']
        if 'tags' in update_data:
            policy.tags = json.dumps(update_data['tags']) if update_data['tags'] else None

        policy.updated_at = datetime.now()

        # Update sections if provided
        if 'sections' in update_data:
            self._update_sections(policy, update_data['sections'])

        self.db.commit()
        self.db.refresh(policy)

        logger.info(f"Updated policy {policy_id}")
        return policy

    def delete_policy(self, policy_id: str, company_id: str) -> bool:
        """
        Delete a policy and all related records.

        Args:
            policy_id: Policy ID to delete
            company_id: Company ID for security

        Returns:
            True if deleted successfully

        Note:
            CASCADE delete will automatically remove:
            - PolicySection records
            - PolicyVersion records
            Vector store cleanup should be done separately
        """
        policy = self.get_policy(policy_id, company_id)
        if not policy:
            return False

        # Delete file from disk
        try:
            file_path = Path(policy.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {policy.file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {policy.file_path}: {e}")

        # Delete policy (CASCADE will handle sections and versions)
        self.db.delete(policy)
        self.db.commit()

        logger.info(f"Deleted policy {policy_id}")
        return True

    def _create_version_snapshot(
        self,
        policy: Policy,
        user_id: str,
        change_description: Optional[str]
    ):
        """Create a version snapshot before updating policy."""
        # Get current version number
        latest_version = self.db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == policy.id
        ).order_by(PolicyVersion.version_number.desc()).first()

        version_number = (latest_version.version_number + 1) if latest_version else 1

        # Create snapshot of current state
        snapshot = policy.to_dict(include_sections=True)

        version = PolicyVersion(
            id=str(uuid.uuid4()),
            policy_id=policy.id,
            version_number=version_number,
            snapshot_data=json.dumps(snapshot),
            changed_by_user_id=user_id,
            change_description=change_description,
            created_at=datetime.now()
        )

        self.db.add(version)
        logger.info(f"Created version {version_number} for policy {policy.id}")

    def _update_sections(self, policy: Policy, sections_data: List[Dict]):
        """Update policy sections (add, edit, delete, reorder)."""
        # Get existing section IDs
        existing_section_ids = {s.id for s in policy.sections}
        updated_section_ids = {s.get('id') for s in sections_data if s.get('id')}

        # Delete sections not in updated list
        sections_to_delete = existing_section_ids - updated_section_ids
        for section_id in sections_to_delete:
            section = self.db.query(PolicySection).get(section_id)
            if section:
                self.db.delete(section)
                logger.info(f"Deleted section {section_id}")

        # Update or create sections
        for section_data in sections_data:
            section_id = section_data.get('id')

            if section_id and section_id in existing_section_ids:
                # Update existing section
                section = self.db.query(PolicySection).get(section_id)
                if section:
                    section.section_number = section_data.get('section_number')
                    section.section_title = section_data.get('section_title')
                    section.section_content = section_data['section_content']
                    section.section_order = section_data['section_order']
                    section.section_type = section_data.get('section_type')
                    section.parent_section_id = section_data.get('parent_section_id')
                    section.updated_at = datetime.now()
                    logger.info(f"Updated section {section_id}")
            else:
                # Create new section
                new_section = PolicySection(
                    id=str(uuid.uuid4()),
                    policy_id=policy.id,
                    section_number=section_data.get('section_number'),
                    section_title=section_data.get('section_title'),
                    section_content=section_data['section_content'],
                    section_order=section_data['section_order'],
                    section_type=section_data.get('section_type'),
                    parent_section_id=section_data.get('parent_section_id'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.db.add(new_section)
                logger.info(f"Created new section for policy {policy.id}")

    def _validate_policy_update(self, policy: Policy, update_data: Dict, company_id: str):
        """Validate policy update data."""
        # Check required title
        if 'title' in update_data:
            if not update_data['title'] or len(update_data['title'].strip()) == 0:
                raise ValueError("Title is required and cannot be empty")

        # Check for duplicate policy_number within company
        if 'policy_number' in update_data and update_data['policy_number']:
            existing = self.db.query(Policy).filter(
                Policy.company_id == company_id,
                Policy.policy_number == update_data['policy_number'],
                Policy.id != policy.id
            ).first()

            if existing:
                raise ValueError(f"Policy number {update_data['policy_number']} already exists")

        # Validate status
        if 'status' in update_data:
            if update_data['status'] not in ['active', 'archived', 'draft']:
                raise ValueError(f"Invalid status: {update_data['status']}")

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None

        # Try different date formats
        formats = [
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%m-%d-%Y',
            '%d-%m-%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None
