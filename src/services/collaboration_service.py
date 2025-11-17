"""
Collaboration Service for Real-Time Document Editing.

This service provides Y.js-based collaborative editing using pycrdt-websocket.
It manages document rooms, syncs state between clients, and persists changes.
"""

import logging
import base64
from typing import Dict, Any, Optional
from datetime import datetime

from pycrdt import Doc, Text
from pycrdt.websocket import WebsocketServer, YRoom

logger = logging.getLogger(__name__)


class CollaborationService:
    """Manages collaborative editing sessions for documents."""

    def __init__(self):
        """Initialize the collaboration service."""
        self.websocket_server = WebsocketServer(
            rooms_ready=True,
            auto_clean_rooms=False,  # We manage room lifecycle manually
            exception_handler=self._exception_handler,
            log=logger,
        )
        # Track awareness state for each room
        self.awareness_states: Dict[str, Dict[int, Any]] = {}
        # Track when rooms were last accessed
        self.room_access_times: Dict[str, datetime] = {}
        logger.info("CollaborationService initialized")

    def _exception_handler(self, exception: Exception, log: logging.Logger) -> bool:
        """Handle exceptions in WebSocket server."""
        log.error(f"Collaboration error: {exception}", exc_info=exception)
        return True  # Exception was handled (logged)

    async def get_room(self, document_id: str) -> YRoom:
        """
        Get or create a collaboration room for a document.

        Args:
            document_id: The document ID (used as room name)

        Returns:
            The YRoom instance for this document
        """
        room = await self.websocket_server.get_room(document_id)
        self.room_access_times[document_id] = datetime.now()

        if document_id not in self.awareness_states:
            self.awareness_states[document_id] = {}

        logger.info(f"Got room for document {document_id}")
        return room

    async def load_document_state(
        self, document_id: str, state_vector: Optional[bytes] = None
    ) -> YRoom:
        """
        Load a document with optional initial state.

        Args:
            document_id: The document ID
            state_vector: Optional Y.js state vector to initialize with

        Returns:
            The initialized YRoom
        """
        room = await self.get_room(document_id)

        if state_vector and not room.ready:
            try:
                # Apply the saved state to the room's document
                room.ydoc.apply_update(state_vector)
                logger.info(f"Applied saved state to document {document_id}")
            except Exception as e:
                logger.error(f"Failed to apply saved state: {e}")

        return room

    def get_document_state(self, document_id: str) -> Optional[bytes]:
        """
        Get the current Y.js state for a document.

        Args:
            document_id: The document ID

        Returns:
            The Y.js state as bytes, or None if room doesn't exist
        """
        if document_id not in self.websocket_server.rooms:
            return None

        room = self.websocket_server.rooms[document_id]
        try:
            state = room.ydoc.get_update()
            logger.info(f"Got state for document {document_id}: {len(state)} bytes")
            return state
        except Exception as e:
            logger.error(f"Failed to get document state: {e}")
            return None

    def get_document_state_base64(self, document_id: str) -> Optional[str]:
        """
        Get the current Y.js state as base64 string (for database storage).

        Args:
            document_id: The document ID

        Returns:
            Base64-encoded state string, or None
        """
        state = self.get_document_state(document_id)
        if state:
            return base64.b64encode(state).decode('utf-8')
        return None

    def get_active_rooms(self) -> Dict[str, int]:
        """
        Get list of active rooms and their client counts.

        Returns:
            Dictionary of room_id -> client count
        """
        result = {}
        for room_id, room in self.websocket_server.rooms.items():
            result[room_id] = len(room.clients)
        return result

    def get_room_clients(self, document_id: str) -> int:
        """
        Get number of clients connected to a room.

        Args:
            document_id: The document ID

        Returns:
            Number of connected clients
        """
        if document_id not in self.websocket_server.rooms:
            return 0
        return len(self.websocket_server.rooms[document_id].clients)

    def update_awareness(
        self, document_id: str, client_id: int, state: Dict[str, Any]
    ) -> None:
        """
        Update awareness state for a client.

        Args:
            document_id: The document ID
            client_id: The client ID
            state: The awareness state (user info, cursor, selection)
        """
        if document_id not in self.awareness_states:
            self.awareness_states[document_id] = {}

        self.awareness_states[document_id][client_id] = {
            **state,
            "lastUpdate": datetime.now().isoformat()
        }
        logger.debug(f"Updated awareness for client {client_id} in {document_id}")

    def remove_awareness(self, document_id: str, client_id: int) -> None:
        """
        Remove awareness state for a disconnected client.

        Args:
            document_id: The document ID
            client_id: The client ID
        """
        if document_id in self.awareness_states:
            self.awareness_states[document_id].pop(client_id, None)
            logger.debug(f"Removed awareness for client {client_id} in {document_id}")

    def get_awareness_states(self, document_id: str) -> Dict[int, Any]:
        """
        Get all awareness states for a document.

        Args:
            document_id: The document ID

        Returns:
            Dictionary of client_id -> awareness state
        """
        return self.awareness_states.get(document_id, {})

    async def cleanup_idle_rooms(self, max_idle_minutes: int = 30) -> int:
        """
        Clean up rooms that have been idle for too long.

        Args:
            max_idle_minutes: Maximum idle time before cleanup

        Returns:
            Number of rooms cleaned up
        """
        from datetime import timedelta

        now = datetime.now()
        rooms_to_remove = []

        for room_id, room in self.websocket_server.rooms.items():
            # Skip rooms with active clients
            if room.clients:
                self.room_access_times[room_id] = now
                continue

            last_access = self.room_access_times.get(room_id, now)
            idle_time = now - last_access

            if idle_time > timedelta(minutes=max_idle_minutes):
                rooms_to_remove.append(room_id)

        for room_id in rooms_to_remove:
            try:
                await self.websocket_server.delete_room(name=room_id)
                self.awareness_states.pop(room_id, None)
                self.room_access_times.pop(room_id, None)
                logger.info(f"Cleaned up idle room: {room_id}")
            except Exception as e:
                logger.error(f"Failed to cleanup room {room_id}: {e}")

        return len(rooms_to_remove)

    async def start(self) -> None:
        """Start the collaboration service."""
        logger.info("Starting CollaborationService...")
        # The websocket_server will be started when we enter its context
        # This is handled by the __aenter__ method

    async def stop(self) -> None:
        """Stop the collaboration service and persist all room states."""
        logger.info("Stopping CollaborationService...")

        # Get all room states before stopping
        final_states = {}
        for room_id in list(self.websocket_server.rooms.keys()):
            state = self.get_document_state(room_id)
            if state:
                final_states[room_id] = state

        # Stop the websocket server
        try:
            await self.websocket_server.stop()
        except Exception as e:
            logger.error(f"Error stopping websocket server: {e}")

        logger.info(f"CollaborationService stopped. Final states for {len(final_states)} rooms captured.")
        return final_states


# Global instance
collaboration_service = CollaborationService()
