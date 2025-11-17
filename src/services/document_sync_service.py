"""
Document Synchronization Service for Real-Time Collaboration.

This service manages WebSocket connections for collaborative editing using Yjs.
It handles:
- Broadcasting document updates to all connected clients
- Managing active connections per document
- Periodic state persistence to database
"""

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DocumentSyncService:
    """Manages real-time document synchronization via WebSockets."""

    def __init__(self):
        # Maps document_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Maps document_id -> last update timestamp
        self.last_updates: Dict[str, datetime] = {}

        # Maps document_id -> Yjs state (as bytes)
        self.document_states: Dict[str, bytes] = {}

    async def connect(self, websocket: WebSocket, document_id: str, user_id: str):
        """
        Connect a client to a document room.

        Args:
            websocket: WebSocket connection (must be already accepted)
            document_id: ID of the document
            user_id: ID of the connecting user
        """
        # Add connection to document room
        if document_id not in self.active_connections:
            self.active_connections[document_id] = set()

        self.active_connections[document_id].add(websocket)

        logger.info(f"User {user_id} connected to document {document_id}. "
                   f"Total connections: {len(self.active_connections[document_id])}")

        # Send current state to new client if available
        if document_id in self.document_states:
            try:
                await websocket.send_bytes(self.document_states[document_id])
                logger.info(f"Sent existing state to user {user_id} for document {document_id}")
            except Exception as e:
                logger.error(f"Failed to send initial state: {e}")

    def disconnect(self, websocket: WebSocket, document_id: str, user_id: str):
        """
        Disconnect a client from a document room.

        Args:
            websocket: WebSocket connection
            document_id: ID of the document
            user_id: ID of the disconnecting user
        """
        if document_id in self.active_connections:
            self.active_connections[document_id].discard(websocket)

            # Clean up empty rooms
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
                logger.info(f"Removed empty room for document {document_id}")

            logger.info(f"User {user_id} disconnected from document {document_id}")

    async def broadcast_update(
        self,
        document_id: str,
        update_data: bytes,
        sender: WebSocket
    ):
        """
        Broadcast a Yjs update to all connected clients except sender.

        Args:
            document_id: ID of the document
            update_data: Yjs update as bytes
            sender: WebSocket connection that sent the update
        """
        if document_id not in self.active_connections:
            logger.warning(f"No active connections for document {document_id}")
            return

        # Update document state
        self.document_states[document_id] = update_data
        self.last_updates[document_id] = datetime.now()

        # Broadcast to all clients except sender
        disconnected = []
        for connection in self.active_connections[document_id]:
            if connection != sender:
                try:
                    await connection.send_bytes(update_data)
                except Exception as e:
                    logger.error(f"Failed to broadcast update: {e}")
                    disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections[document_id].discard(conn)

        logger.debug(f"Broadcasted update for document {document_id} to "
                    f"{len(self.active_connections[document_id]) - 1} clients")

    async def handle_client_message(
        self,
        websocket: WebSocket,
        document_id: str,
        user_id: str,
        message: bytes
    ):
        """
        Handle a message from a client.

        Args:
            websocket: WebSocket connection
            document_id: ID of the document
            user_id: ID of the user
            message: Message data (Yjs update)
        """
        try:
            logger.info(f"Received message from user {user_id} in document {document_id}: {len(message)} bytes")

            # Broadcast the update to other clients
            await self.broadcast_update(document_id, message, websocket)

            logger.info(f"Broadcasted update to {len(self.active_connections.get(document_id, set())) - 1} clients")

        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await websocket.send_json({
                "type": "error",
                "message": "Failed to process update"
            })

    async def persist_state(
        self,
        document_id: str,
        db: Session
    ):
        """
        Persist current document state to database.

        Args:
            document_id: ID of the document
            db: Database session
        """
        if document_id not in self.document_states:
            return

        try:
            from ..database import Document

            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                # Store Yjs state as base64
                import base64
                state_b64 = base64.b64encode(self.document_states[document_id]).decode('utf-8')
                doc.yjs_state_vector = state_b64
                db.commit()

                logger.info(f"Persisted state for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to persist document state: {e}")

    def get_connection_count(self, document_id: str) -> int:
        """Get number of active connections for a document."""
        return len(self.active_connections.get(document_id, set()))

    async def send_user_joined(
        self,
        document_id: str,
        user_id: str,
        user_name: str
    ):
        """
        Notify all clients that a user joined.

        Args:
            document_id: ID of the document
            user_id: ID of the user
            user_name: Name of the user
        """
        if document_id not in self.active_connections:
            return

        message = json.dumps({
            "type": "user_joined",
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now().isoformat()
        })

        for connection in self.active_connections[document_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send user_joined event: {e}")

    async def send_user_left(
        self,
        document_id: str,
        user_id: str
    ):
        """
        Notify all clients that a user left.

        Args:
            document_id: ID of the document
            user_id: ID of the user
        """
        if document_id not in self.active_connections:
            return

        message = json.dumps({
            "type": "user_left",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })

        for connection in self.active_connections[document_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send user_left event: {e}")


# Global instance
document_sync_service = DocumentSyncService()
