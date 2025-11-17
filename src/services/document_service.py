"""Document service for collaborative editor."""

import logging
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from ..database.models import Document, DocumentCollaborator, User

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing collaborative documents."""

    def __init__(self, db: DBSession):
        """
        Initialize document service.

        Args:
            db: Database session
        """
        self.db = db

    def create_document(
        self,
        title: str,
        created_by_user_id: str,
        negotiation_id: Optional[str] = None,
        analysis_job_id: Optional[str] = None,
        import_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new document.

        Args:
            title: Document title
            created_by_user_id: User ID of creator
            negotiation_id: Optional link to negotiation
            analysis_job_id: Optional link to AI analysis
            import_source: Optional source ('original', 'ai_redlined')

        Returns:
            Dictionary with success status and document data
        """
        try:
            document_id = str(uuid.uuid4())

            document = Document(
                id=document_id,
                title=title,
                created_by_user_id=created_by_user_id,
                negotiation_id=negotiation_id,
                analysis_job_id=analysis_job_id,
                import_source=import_source,
                yjs_state_vector=None,  # Empty initially
                status='draft'
            )
            self.db.add(document)

            # Add creator as collaborator
            collaborator = DocumentCollaborator(
                id=str(uuid.uuid4()),
                document_id=document_id,
                user_id=created_by_user_id,
                permission='edit',
                added_by_user_id=created_by_user_id
            )
            self.db.add(collaborator)

            # If linked to negotiation, add both participants as collaborators
            if negotiation_id:
                from ..database.models import Negotiation
                negotiation = self.db.query(Negotiation).filter(
                    Negotiation.id == negotiation_id
                ).first()

                if negotiation:
                    # Add initiator if not already added
                    if negotiation.initiator_user_id != created_by_user_id:
                        collaborator_initiator = DocumentCollaborator(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            user_id=negotiation.initiator_user_id,
                            permission='edit',
                            added_by_user_id=created_by_user_id
                        )
                        self.db.add(collaborator_initiator)

                    # Add receiver if not already added
                    if negotiation.receiver_user_id != created_by_user_id:
                        collaborator_receiver = DocumentCollaborator(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            user_id=negotiation.receiver_user_id,
                            permission='edit',
                            added_by_user_id=created_by_user_id
                        )
                        self.db.add(collaborator_receiver)

            self.db.commit()
            logger.info(f"Created document {document_id}: {title}")

            return {
                "success": True,
                "document": document.to_dict()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating document: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_document(
        self,
        document_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get document by ID with access control check.

        Args:
            document_id: Document ID
            user_id: User ID requesting access

        Returns:
            Dictionary with success status and document data
        """
        try:
            # Check access
            if not self.can_user_access(document_id, user_id):
                return {
                    "success": False,
                    "error": "Access denied - you are not a collaborator on this document"
                }

            document = self.db.query(Document).filter(
                Document.id == document_id
            ).first()

            if not document:
                return {
                    "success": False,
                    "error": "Document not found"
                }

            return {
                "success": True,
                "document": document.to_dict()
            }

        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_user_documents(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List documents accessible by user.

        Args:
            user_id: User ID
            limit: Maximum number of documents
            offset: Offset for pagination

        Returns:
            Dictionary with success status and documents list
        """
        try:
            # Get documents where user is a collaborator
            documents = self.db.query(Document).join(
                DocumentCollaborator,
                Document.id == DocumentCollaborator.document_id
            ).filter(
                DocumentCollaborator.user_id == user_id
            ).order_by(
                Document.updated_at.desc()
            ).limit(limit).offset(offset).all()

            # Get total count
            total = self.db.query(func.count(Document.id)).join(
                DocumentCollaborator,
                Document.id == DocumentCollaborator.document_id
            ).filter(
                DocumentCollaborator.user_id == user_id
            ).scalar()

            return {
                "success": True,
                "documents": [doc.to_dict() for doc in documents],
                "total": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error listing documents for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_document(
        self,
        document_id: str,
        user_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
        lexical_state: Optional[str] = None,
        yjs_state_vector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update document metadata or content.

        Args:
            document_id: Document ID
            user_id: User ID making update
            title: New title (optional)
            status: New status (optional)
            lexical_state: New Lexical content (optional)
            yjs_state_vector: New Yjs state (optional)

        Returns:
            Dictionary with success status
        """
        try:
            # Check access
            if not self.can_user_access(document_id, user_id):
                return {
                    "success": False,
                    "error": "Access denied"
                }

            document = self.db.query(Document).filter(
                Document.id == document_id
            ).first()

            if not document:
                return {
                    "success": False,
                    "error": "Document not found"
                }

            # Update fields if provided
            if title is not None:
                document.title = title

            if status is not None:
                document.status = status

            if lexical_state is not None:
                document.lexical_state = lexical_state

            if yjs_state_vector is not None:
                document.yjs_state_vector = yjs_state_vector

            document.updated_at = datetime.now()
            self.db.commit()

            logger.info(f"Updated document {document_id}")

            return {
                "success": True,
                "document": document.to_dict()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating document {document_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def delete_document(
        self,
        document_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Delete document (only creator can delete).

        Args:
            document_id: Document ID
            user_id: User ID requesting deletion

        Returns:
            Dictionary with success status
        """
        try:
            document = self.db.query(Document).filter(
                Document.id == document_id
            ).first()

            if not document:
                return {
                    "success": False,
                    "error": "Document not found"
                }

            # Only creator can delete
            if document.created_by_user_id != user_id:
                return {
                    "success": False,
                    "error": "Only the document creator can delete it"
                }

            self.db.delete(document)
            self.db.commit()

            logger.info(f"Deleted document {document_id}")

            return {
                "success": True,
                "message": "Document deleted successfully"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting document {document_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def can_user_access(
        self,
        document_id: str,
        user_id: str
    ) -> bool:
        """
        Check if user has access to document.

        Args:
            document_id: Document ID
            user_id: User ID

        Returns:
            True if user is a collaborator, False otherwise
        """
        collaborator = self.db.query(DocumentCollaborator).filter(
            DocumentCollaborator.document_id == document_id,
            DocumentCollaborator.user_id == user_id
        ).first()

        return collaborator is not None

    def add_collaborator(
        self,
        document_id: str,
        user_id: str,
        added_by_user_id: str,
        permission: str = 'edit'
    ) -> Dict[str, Any]:
        """
        Add a collaborator to document.

        Args:
            document_id: Document ID
            user_id: User ID or email to add
            added_by_user_id: User ID adding the collaborator
            permission: Permission level (default: 'edit')

        Returns:
            Dictionary with success status
        """
        try:
            # Check if requester has access
            if not self.can_user_access(document_id, added_by_user_id):
                return {
                    "success": False,
                    "error": "Access denied"
                }

            # If user_id looks like an email, lookup by email
            if '@' in user_id:
                logger.info(f"Looking up user by email: {user_id}")
                user = self.db.query(User).filter(User.email == user_id).first()
                if not user:
                    logger.error(f"No user found with email: {user_id}")
                    # List all users for debugging
                    all_users = self.db.query(User).all()
                    logger.info(f"Available users: {[u.email for u in all_users]}")
                    return {
                        "success": False,
                        "error": f"No user found with email: {user_id}"
                    }
                actual_user_id = user.id
                logger.info(f"Found user {user.email} with ID: {actual_user_id}")
            else:
                actual_user_id = user_id
                # Verify user exists
                user = self.db.query(User).filter(User.id == actual_user_id).first()
                if not user:
                    return {
                        "success": False,
                        "error": "User not found"
                    }

            # Check if user already a collaborator
            existing = self.db.query(DocumentCollaborator).filter(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == actual_user_id
            ).first()

            if existing:
                return {
                    "success": False,
                    "error": "User is already a collaborator"
                }

            # Add collaborator
            collaborator = DocumentCollaborator(
                id=str(uuid.uuid4()),
                document_id=document_id,
                user_id=actual_user_id,
                permission=permission,
                added_by_user_id=added_by_user_id
            )
            self.db.add(collaborator)
            self.db.commit()

            logger.info(f"Added collaborator {actual_user_id} ({user.email}) to document {document_id}")

            return {
                "success": True,
                "collaborator": collaborator.to_dict()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding collaborator: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_collaborators(
        self,
        document_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get list of collaborators for document.

        Args:
            document_id: Document ID
            user_id: User ID requesting list

        Returns:
            Dictionary with success status and collaborators list
        """
        try:
            # Check access
            if not self.can_user_access(document_id, user_id):
                return {
                    "success": False,
                    "error": "Access denied"
                }

            collaborators = self.db.query(DocumentCollaborator).filter(
                DocumentCollaborator.document_id == document_id
            ).all()

            return {
                "success": True,
                "collaborators": [c.to_dict() for c in collaborators]
            }

        except Exception as e:
            logger.error(f"Error getting collaborators: {e}")
            return {
                "success": False,
                "error": str(e)
            }
