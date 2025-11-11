"""WebSocket manager for real-time negotiation messaging."""

import logging
import json
from typing import Dict, List, Optional
from fastapi import WebSocket
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time messaging."""

    def __init__(self):
        """Initialize WebSocket manager."""
        # Structure: {negotiation_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, negotiation_id: str, user_id: str, websocket: WebSocket):
        """
        Register a WebSocket connection.

        Note: The connection should already be accepted before calling this method.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user
            websocket: WebSocket connection (already accepted)
        """
        # Initialize negotiation room if it doesn't exist
        if negotiation_id not in self.active_connections:
            self.active_connections[negotiation_id] = {}

        # Register connection
        self.active_connections[negotiation_id][user_id] = websocket

        logger.info(f"User {user_id} connected to negotiation {negotiation_id}")

        # Notify others that user joined
        await self.broadcast_to_negotiation(
            negotiation_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": self._get_timestamp()
            },
            exclude_user=user_id
        )

    async def disconnect(self, negotiation_id: str, user_id: str):
        """
        Remove a WebSocket connection.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user
        """
        if negotiation_id in self.active_connections:
            if user_id in self.active_connections[negotiation_id]:
                del self.active_connections[negotiation_id][user_id]

                logger.info(f"User {user_id} disconnected from negotiation {negotiation_id}")

                # Notify others that user left
                await self.broadcast_to_negotiation(
                    negotiation_id,
                    {
                        "type": "user_left",
                        "user_id": user_id,
                        "timestamp": self._get_timestamp()
                    }
                )

                # Clean up empty negotiation rooms
                if not self.active_connections[negotiation_id]:
                    del self.active_connections[negotiation_id]
                    logger.info(f"Removed empty negotiation room {negotiation_id}")

    async def send_to_user(self, negotiation_id: str, user_id: str, message: dict):
        """
        Send a message to a specific user.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user
            message: Message dictionary
        """
        if negotiation_id in self.active_connections:
            if user_id in self.active_connections[negotiation_id]:
                websocket = self.active_connections[negotiation_id][user_id]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {str(e)}")
                    # Connection might be dead, remove it
                    await self.disconnect(negotiation_id, user_id)

    async def broadcast_to_negotiation(
        self,
        negotiation_id: str,
        message: dict,
        exclude_user: Optional[str] = None
    ):
        """
        Broadcast a message to all users in a negotiation.

        Args:
            negotiation_id: ID of the negotiation
            message: Message dictionary
            exclude_user: Optional user ID to exclude from broadcast
        """
        if negotiation_id not in self.active_connections:
            return

        # Get all connected users
        connections = self.active_connections[negotiation_id].copy()

        for user_id, websocket in connections.items():
            # Skip excluded user
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                # Connection might be dead, remove it
                await self.disconnect(negotiation_id, user_id)

    def get_online_users(self, negotiation_id: str) -> List[str]:
        """
        Get list of online users in a negotiation.

        Args:
            negotiation_id: ID of the negotiation

        Returns:
            List of user IDs currently connected
        """
        if negotiation_id in self.active_connections:
            return list(self.active_connections[negotiation_id].keys())
        return []

    def is_user_online(self, negotiation_id: str, user_id: str) -> bool:
        """
        Check if a user is online in a negotiation.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user

        Returns:
            True if user is connected, False otherwise
        """
        return (
            negotiation_id in self.active_connections
            and user_id in self.active_connections[negotiation_id]
        )

    async def send_typing_indicator(
        self,
        negotiation_id: str,
        user_id: str,
        is_typing: bool
    ):
        """
        Send typing indicator to other users in negotiation.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user typing
            is_typing: True if typing, False if stopped
        """
        await self.broadcast_to_negotiation(
            negotiation_id,
            {
                "type": "typing",
                "user_id": user_id,
                "is_typing": is_typing,
                "timestamp": self._get_timestamp()
            },
            exclude_user=user_id
        )

    async def send_message_event(
        self,
        negotiation_id: str,
        message_data: dict,
        sender_user_id: str
    ):
        """
        Broadcast a new message to all users in negotiation.

        Args:
            negotiation_id: ID of the negotiation
            message_data: Message data dictionary
            sender_user_id: ID of the user who sent the message
        """
        await self.broadcast_to_negotiation(
            negotiation_id,
            {
                "type": "message",
                **message_data
            }
        )

    async def send_read_receipt(
        self,
        negotiation_id: str,
        message_ids: List[str],
        reader_user_id: str
    ):
        """
        Notify that messages have been read.

        Args:
            negotiation_id: ID of the negotiation
            message_ids: List of message IDs that were read
            reader_user_id: ID of the user who read the messages
        """
        await self.broadcast_to_negotiation(
            negotiation_id,
            {
                "type": "read",
                "message_ids": message_ids,
                "reader_user_id": reader_user_id,
                "timestamp": self._get_timestamp()
            },
            exclude_user=reader_user_id
        )

    async def send_acknowledgment(
        self,
        negotiation_id: str,
        user_id: str,
        message_id: str
    ):
        """
        Send acknowledgment to sender that message was received.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the sender
            message_id: ID of the message
        """
        await self.send_to_user(
            negotiation_id,
            user_id,
            {
                "type": "ack",
                "message_id": message_id,
                "timestamp": self._get_timestamp()
            }
        )

    async def send_error(
        self,
        negotiation_id: str,
        user_id: str,
        error_code: str,
        error_message: str
    ):
        """
        Send error message to a user.

        Args:
            negotiation_id: ID of the negotiation
            user_id: ID of the user
            error_code: Error code
            error_message: Human-readable error message
        """
        await self.send_to_user(
            negotiation_id,
            user_id,
            {
                "type": "error",
                "code": error_code,
                "message": error_message,
                "timestamp": self._get_timestamp()
            }
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        count = 0
        for negotiation_connections in self.active_connections.values():
            count += len(negotiation_connections)
        return count

    def get_negotiation_count(self) -> int:
        """Get number of active negotiation rooms."""
        return len(self.active_connections)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
