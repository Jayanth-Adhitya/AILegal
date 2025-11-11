"""Service for managing contract negotiations between parties."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import or_, and_

from ..database.models import Negotiation, User, NegotiationMessage

logger = logging.getLogger(__name__)


class NegotiationService:
    """Service for managing negotiations."""

    def __init__(self, db: DBSession):
        """Initialize negotiation service with database session."""
        self.db = db

    def create_negotiation(
        self,
        initiator_id: str,
        receiver_email: str,
        contract_name: str,
        contract_job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new negotiation request.

        Args:
            initiator_id: User ID of the initiator
            receiver_email: Email of the receiver
            contract_name: Name of the contract being negotiated
            contract_job_id: Optional reference to analysis job

        Returns:
            Dictionary with success status and negotiation data or error message
        """
        try:
            # Get initiator
            initiator = self.db.query(User).filter(User.id == initiator_id).first()
            if not initiator:
                return {"success": False, "error": "Initiator not found"}

            # Get receiver by email
            receiver = self.db.query(User).filter(User.email == receiver_email.lower()).first()
            if not receiver:
                return {"success": False, "error": f"User with email {receiver_email} not found"}

            # Check if receiver is from different company
            if initiator.company_id == receiver.company_id:
                return {"success": False, "error": "Cannot negotiate with users from the same company"}

            # Check for existing active negotiation with same parties and contract
            existing = self.db.query(Negotiation).filter(
                and_(
                    Negotiation.contract_name == contract_name,
                    or_(
                        and_(
                            Negotiation.initiator_user_id == initiator_id,
                            Negotiation.receiver_user_id == receiver.id
                        ),
                        and_(
                            Negotiation.initiator_user_id == receiver.id,
                            Negotiation.receiver_user_id == initiator_id
                        )
                    ),
                    Negotiation.status.in_(["pending", "active"])
                )
            ).first()

            if existing:
                return {
                    "success": False,
                    "error": "Active negotiation already exists for this contract between these parties",
                    "existing_negotiation_id": existing.id
                }

            # Create negotiation
            negotiation = Negotiation(
                id=str(uuid.uuid4()),
                contract_name=contract_name,
                contract_job_id=contract_job_id,
                initiator_user_id=initiator_id,
                receiver_user_id=receiver.id,
                status="pending",
                created_at=datetime.now()
            )

            self.db.add(negotiation)

            # Create system message
            system_msg = NegotiationMessage(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation.id,
                sender_user_id=None,
                sender_type="system",
                content=f"{initiator.company_name} initiated a negotiation request for '{contract_name}'",
                message_type="system",
                created_at=datetime.now()
            )

            self.db.add(system_msg)
            self.db.commit()

            logger.info(f"Created negotiation {negotiation.id} between {initiator.company_name} and {receiver.company_name}")

            return {
                "success": True,
                "negotiation": negotiation.to_dict()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating negotiation: {str(e)}")
            return {"success": False, "error": f"Failed to create negotiation: {str(e)}"}

    def accept_negotiation(self, negotiation_id: str, user_id: str) -> Dict[str, Any]:
        """
        Accept a pending negotiation request.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user accepting (must be receiver)

        Returns:
            Dictionary with success status and updated negotiation or error
        """
        try:
            negotiation = self.db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
            if not negotiation:
                return {"success": False, "error": "Negotiation not found"}

            # Verify user is the receiver
            if negotiation.receiver_user_id != user_id:
                return {"success": False, "error": "Only the receiver can accept a negotiation request"}

            # Verify status is pending
            if negotiation.status != "pending":
                return {"success": False, "error": f"Cannot accept negotiation with status: {negotiation.status}"}

            # Update status
            negotiation.status = "active"
            negotiation.accepted_at = datetime.now()

            # Create system message
            receiver = self.db.query(User).filter(User.id == user_id).first()
            system_msg = NegotiationMessage(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation.id,
                sender_user_id=None,
                sender_type="system",
                content=f"{receiver.company_name} accepted the negotiation request",
                message_type="system",
                created_at=datetime.now()
            )

            self.db.add(system_msg)
            self.db.commit()

            logger.info(f"Negotiation {negotiation_id} accepted by user {user_id}")

            return {
                "success": True,
                "negotiation": negotiation.to_dict()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error accepting negotiation: {str(e)}")
            return {"success": False, "error": f"Failed to accept negotiation: {str(e)}"}

    def reject_negotiation(self, negotiation_id: str, user_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Reject a pending negotiation request.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user rejecting (must be receiver)
            reason: Optional reason for rejection

        Returns:
            Dictionary with success status
        """
        try:
            negotiation = self.db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
            if not negotiation:
                return {"success": False, "error": "Negotiation not found"}

            # Verify user is the receiver
            if negotiation.receiver_user_id != user_id:
                return {"success": False, "error": "Only the receiver can reject a negotiation request"}

            # Verify status is pending
            if negotiation.status != "pending":
                return {"success": False, "error": f"Cannot reject negotiation with status: {negotiation.status}"}

            # Update status
            negotiation.status = "rejected"

            # Create system message
            receiver = self.db.query(User).filter(User.id == user_id).first()
            content = f"{receiver.company_name} rejected the negotiation request"
            if reason:
                content += f": {reason}"

            system_msg = NegotiationMessage(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation.id,
                sender_user_id=None,
                sender_type="system",
                content=content,
                message_type="system",
                created_at=datetime.now()
            )

            self.db.add(system_msg)
            self.db.commit()

            logger.info(f"Negotiation {negotiation_id} rejected by user {user_id}")

            return {"success": True}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error rejecting negotiation: {str(e)}")
            return {"success": False, "error": f"Failed to reject negotiation: {str(e)}"}

    def complete_negotiation(self, negotiation_id: str, user_id: str) -> Dict[str, Any]:
        """
        Mark a negotiation as completed.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user completing (must be participant)

        Returns:
            Dictionary with success status
        """
        try:
            negotiation = self.db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
            if not negotiation:
                return {"success": False, "error": "Negotiation not found"}

            # Verify user is a participant
            if negotiation.initiator_user_id != user_id and negotiation.receiver_user_id != user_id:
                return {"success": False, "error": "Only participants can complete a negotiation"}

            # Verify status is active
            if negotiation.status != "active":
                return {"success": False, "error": f"Cannot complete negotiation with status: {negotiation.status}"}

            # Update status
            negotiation.status = "completed"
            negotiation.completed_at = datetime.now()

            # Create system message
            user = self.db.query(User).filter(User.id == user_id).first()
            system_msg = NegotiationMessage(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation.id,
                sender_user_id=None,
                sender_type="system",
                content=f"{user.company_name} marked the negotiation as completed",
                message_type="system",
                created_at=datetime.now()
            )

            self.db.add(system_msg)
            self.db.commit()

            logger.info(f"Negotiation {negotiation_id} completed by user {user_id}")

            return {"success": True}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing negotiation: {str(e)}")
            return {"success": False, "error": f"Failed to complete negotiation: {str(e)}"}

    def cancel_negotiation(self, negotiation_id: str, user_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a negotiation.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user cancelling (must be participant)
            reason: Optional reason for cancellation

        Returns:
            Dictionary with success status
        """
        try:
            negotiation = self.db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
            if not negotiation:
                return {"success": False, "error": "Negotiation not found"}

            # Verify user is a participant
            if negotiation.initiator_user_id != user_id and negotiation.receiver_user_id != user_id:
                return {"success": False, "error": "Only participants can cancel a negotiation"}

            # Update status
            negotiation.status = "cancelled"

            # Create system message
            user = self.db.query(User).filter(User.id == user_id).first()
            content = f"{user.company_name} cancelled the negotiation"
            if reason:
                content += f": {reason}"

            system_msg = NegotiationMessage(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation.id,
                sender_user_id=None,
                sender_type="system",
                content=content,
                message_type="system",
                created_at=datetime.now()
            )

            self.db.add(system_msg)
            self.db.commit()

            logger.info(f"Negotiation {negotiation_id} cancelled by user {user_id}")

            return {"success": True}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling negotiation: {str(e)}")
            return {"success": False, "error": f"Failed to cancel negotiation: {str(e)}"}

    def get_negotiation(self, negotiation_id: str) -> Optional[Negotiation]:
        """
        Get negotiation by ID.

        Args:
            negotiation_id: ID of the negotiation

        Returns:
            Negotiation object or None
        """
        return self.db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()

    def list_user_negotiations(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List all negotiations for a user.

        Args:
            user_id: ID of the user
            status_filter: Optional status filter (pending, active, completed, rejected, cancelled)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dictionary with negotiations list and total count
        """
        try:
            # Build query
            query = self.db.query(Negotiation).filter(
                or_(
                    Negotiation.initiator_user_id == user_id,
                    Negotiation.receiver_user_id == user_id
                )
            )

            # Apply status filter if provided
            if status_filter:
                query = query.filter(Negotiation.status == status_filter)

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            negotiations = query.order_by(Negotiation.created_at.desc()).limit(limit).offset(offset).all()

            return {
                "success": True,
                "negotiations": [neg.to_dict() for neg in negotiations],
                "total": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error listing negotiations: {str(e)}")
            return {"success": False, "error": f"Failed to list negotiations: {str(e)}"}

    def can_user_access(self, negotiation_id: str, user_id: str) -> bool:
        """
        Check if a user can access a negotiation.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user

        Returns:
            True if user is a participant, False otherwise
        """
        negotiation = self.db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
        if not negotiation:
            return False

        return negotiation.initiator_user_id == user_id or negotiation.receiver_user_id == user_id

    def get_unread_count(self, negotiation_id: str, user_id: str) -> int:
        """
        Get count of unread messages for a user in a negotiation.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user

        Returns:
            Count of unread messages
        """
        try:
            count = self.db.query(NegotiationMessage).filter(
                and_(
                    NegotiationMessage.negotiation_id == negotiation_id,
                    NegotiationMessage.sender_user_id != user_id,  # Not sent by this user
                    NegotiationMessage.sender_type == "user",  # Only user messages (not system)
                    NegotiationMessage.read_at == None  # Not read yet
                )
            ).count()

            return count

        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
