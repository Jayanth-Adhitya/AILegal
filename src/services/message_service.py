"""Service for managing negotiation messages."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_

from ..database.models import NegotiationMessage, User

logger = logging.getLogger(__name__)


class MessageService:
    """Service for managing negotiation messages."""

    def __init__(self, db: DBSession):
        """Initialize message service with database session."""
        self.db = db

    def send_message(
        self,
        negotiation_id: str,
        sender_user_id: str,
        content: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Send a message in a negotiation.

        Args:
            negotiation_id: ID of the negotiation
            sender_user_id: ID of the user sending the message
            content: Message content
            message_type: Type of message (text, system)

        Returns:
            Dictionary with success status and message data or error
        """
        try:
            # Validate content length
            if len(content) > 10000:
                return {"success": False, "error": "Message content exceeds 10,000 characters"}

            if not content.strip():
                return {"success": False, "error": "Message content cannot be empty"}

            # Create message
            message = NegotiationMessage(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation_id,
                sender_user_id=sender_user_id,
                sender_type="user",
                content=content,
                message_type=message_type,
                created_at=datetime.now()
            )

            self.db.add(message)
            self.db.commit()

            logger.info(f"Message {message.id} sent in negotiation {negotiation_id} by user {sender_user_id}")

            return {
                "success": True,
                "message": message.to_dict()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error sending message: {str(e)}")
            return {"success": False, "error": f"Failed to send message: {str(e)}"}

    def create_system_message(
        self,
        negotiation_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Create a system message in a negotiation.

        Args:
            negotiation_id: ID of the negotiation
            content: Message content

        Returns:
            Dictionary with success status and message data or error
        """
        try:
            message = NegotiationMessage(
                id=str(uuid.uuid4()),
                negotiation_id=negotiation_id,
                sender_user_id=None,
                sender_type="system",
                content=content,
                message_type="system",
                created_at=datetime.now()
            )

            self.db.add(message)
            self.db.commit()

            logger.info(f"System message {message.id} created in negotiation {negotiation_id}")

            return {
                "success": True,
                "message": message.to_dict()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating system message: {str(e)}")
            return {"success": False, "error": f"Failed to create system message: {str(e)}"}

    def get_message_history(
        self,
        negotiation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get message history for a negotiation.

        Args:
            negotiation_id: ID of the negotiation
            limit: Maximum number of messages to return
            offset: Number of messages to skip (for pagination)

        Returns:
            Dictionary with messages list and metadata
        """
        try:
            # Get total count
            total = self.db.query(NegotiationMessage).filter(
                NegotiationMessage.negotiation_id == negotiation_id
            ).count()

            # Get messages with pagination, ordered by created_at ascending
            messages = self.db.query(NegotiationMessage).filter(
                NegotiationMessage.negotiation_id == negotiation_id
            ).order_by(NegotiationMessage.created_at.asc()).limit(limit).offset(offset).all()

            return {
                "success": True,
                "messages": [msg.to_dict() for msg in messages],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(messages)) < total
            }

        except Exception as e:
            logger.error(f"Error getting message history: {str(e)}")
            return {"success": False, "error": f"Failed to get message history: {str(e)}"}

    def mark_as_read(
        self,
        message_ids: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Mark messages as read by a user.

        Args:
            message_ids: List of message IDs to mark as read
            user_id: ID of the user marking messages as read

        Returns:
            Dictionary with success status
        """
        try:
            # Get messages that belong to the user's negotiations and are not sent by the user
            messages = self.db.query(NegotiationMessage).filter(
                and_(
                    NegotiationMessage.id.in_(message_ids),
                    NegotiationMessage.sender_user_id != user_id,  # Not sent by this user
                    NegotiationMessage.read_at == None  # Not already read
                )
            ).all()

            # Mark as read
            read_at = datetime.now()
            for message in messages:
                message.read_at = read_at

            self.db.commit()

            logger.info(f"Marked {len(messages)} messages as read by user {user_id}")

            return {
                "success": True,
                "marked_count": len(messages)
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking messages as read: {str(e)}")
            return {"success": False, "error": f"Failed to mark messages as read: {str(e)}"}

    def get_unread_count(
        self,
        negotiation_id: str,
        user_id: str
    ) -> int:
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
                    NegotiationMessage.sender_type == "user",  # Only user messages
                    NegotiationMessage.read_at == None  # Not read yet
                )
            ).count()

            return count

        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
