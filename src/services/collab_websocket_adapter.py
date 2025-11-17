"""
WebSocket Adapter for integrating pycrdt-websocket with FastAPI.

This adapter bridges FastAPI WebSocket connections to the pycrdt Channel interface
required by pycrdt-websocket's WebsocketServer.
"""

import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class FastAPIWebSocketAdapter:
    """
    Adapter that makes FastAPI WebSocket compatible with pycrdt.Channel interface.

    pycrdt-websocket expects a channel with:
    - .path property (room name)
    - async iterator interface (__aiter__, __anext__)
    - .send(bytes) method
    - .recv() method that returns bytes
    """

    def __init__(self, websocket: WebSocket, room_name: str):
        """
        Initialize the adapter.

        Args:
            websocket: FastAPI WebSocket connection (must be already accepted)
            room_name: The room name (document_id)
        """
        self._websocket = websocket
        self._room_name = room_name
        self._closed = False
        logger.debug(f"Created adapter for room: {room_name}")

    @property
    def path(self) -> str:
        """Return the room name (required by pycrdt-websocket)."""
        return self._room_name

    def __aiter__(self):
        """Make the adapter an async iterator."""
        return self

    async def __anext__(self) -> bytes:
        """Get next message from WebSocket."""
        try:
            return await self.recv()
        except StopAsyncIteration:
            raise
        except Exception as e:
            logger.error(f"Error in __anext__: {e}")
            raise StopAsyncIteration()

    async def send(self, message: bytes) -> None:
        """
        Send binary message to client.

        Args:
            message: Y.js update as bytes
        """
        if self._closed:
            return
        try:
            await self._websocket.send_bytes(message)
            logger.debug(f"Sent {len(message)} bytes to client in room {self._room_name}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._closed = True
            raise

    async def recv(self) -> bytes:
        """
        Receive binary message from client.

        Returns:
            Y.js update as bytes

        Raises:
            StopAsyncIteration: When connection is closed
        """
        if self._closed:
            raise StopAsyncIteration()
        try:
            message = await self._websocket.receive_bytes()
            logger.debug(f"Received {len(message)} bytes from client in room {self._room_name}")
            return message
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            self._closed = True
            raise StopAsyncIteration()


class CollaborationWebSocketManager:
    """
    Manages collaborative editing WebSocket connections.

    This class handles the lifecycle of pycrdt-websocket server
    and integrates it with FastAPI.
    """

    def __init__(self):
        """Initialize the manager."""
        from .collaboration_service import collaboration_service
        self.collab_service = collaboration_service
        self._started = False
        logger.info("CollaborationWebSocketManager initialized")

    async def start(self) -> None:
        """Start the collaboration WebSocket server."""
        if self._started:
            return

        # Start the websocket server
        logger.info("Starting collaboration WebSocket server...")
        await self.collab_service.websocket_server.__aenter__()
        self._started = True
        logger.info("Collaboration WebSocket server started")

    async def stop(self) -> None:
        """Stop the collaboration WebSocket server."""
        if not self._started:
            return

        logger.info("Stopping collaboration WebSocket server...")
        await self.collab_service.websocket_server.__aexit__(None, None, None)
        self._started = False
        logger.info("Collaboration WebSocket server stopped")

    async def handle_connection(
        self,
        websocket: WebSocket,
        document_id: str,
        user_id: str,
        user_email: str
    ) -> None:
        """
        Handle a new WebSocket connection for collaborative editing.

        Args:
            websocket: FastAPI WebSocket (must be already accepted)
            document_id: The document ID (room name)
            user_id: The user ID
            user_email: The user's email (for awareness)
        """
        if not self._started:
            await self.start()

        # Create adapter for this connection
        adapter = FastAPIWebSocketAdapter(websocket, document_id)

        # Update awareness with user info
        # Generate a unique client ID based on user_id and timestamp
        import time
        client_id = hash(f"{user_id}_{time.time()}") % (2**31)

        self.collab_service.update_awareness(
            document_id,
            client_id,
            {
                "user": {
                    "id": user_id,
                    "email": user_email,
                    "name": user_email,
                    "color": self._get_user_color(user_id)
                },
                "cursor": None,
                "selection": None
            }
        )

        logger.info(f"User {user_email} connected to document {document_id} (client_id: {client_id})")

        try:
            # Let pycrdt-websocket handle the Y.js protocol
            await self.collab_service.websocket_server.serve(adapter)
        except Exception as e:
            logger.error(f"Collaboration connection error: {e}")
        finally:
            # Clean up awareness
            self.collab_service.remove_awareness(document_id, client_id)
            logger.info(f"User {user_email} disconnected from document {document_id}")

    def _get_user_color(self, user_id: str) -> str:
        """
        Generate a consistent color for a user.

        Args:
            user_id: The user ID

        Returns:
            Hex color string
        """
        # List of distinct colors for collaboration
        colors = [
            "#FF5733",  # Red-Orange
            "#33FF57",  # Green
            "#3357FF",  # Blue
            "#FF33F5",  # Pink
            "#F5FF33",  # Yellow
            "#33FFF5",  # Cyan
            "#FF8C33",  # Orange
            "#8C33FF",  # Purple
            "#33FF8C",  # Mint
            "#FF338C",  # Rose
        ]
        # Use hash of user_id to get consistent color
        color_index = hash(user_id) % len(colors)
        return colors[color_index]

    def get_awareness_for_document(self, document_id: str) -> dict:
        """
        Get awareness states for a document.

        Args:
            document_id: The document ID

        Returns:
            Dictionary of awareness states
        """
        return self.collab_service.get_awareness_states(document_id)

    def get_active_rooms(self) -> dict:
        """Get all active rooms and their client counts."""
        return self.collab_service.get_active_rooms()


# Global instance
collab_ws_manager = CollaborationWebSocketManager()
