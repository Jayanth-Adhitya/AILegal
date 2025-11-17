import Fastify from 'fastify';
import fastifyWebsocket from '@fastify/websocket';
import { CollaborationBuilder } from '@superdoc-dev/superdoc-yjs-collaboration';
import dotenv from 'dotenv';
import * as Y from 'yjs';
import { encodeStateAsUpdate } from 'yjs';

dotenv.config();

const PORT = process.env.COLLAB_PORT || 1234;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

const fastify = Fastify({ logger: true });

// Register WebSocket support
await fastify.register(fastifyWebsocket);

/**
 * SuperDoc Collaboration Server
 *
 * Uses the official @superdoc-dev/superdoc-yjs-collaboration package
 * for real-time collaborative editing.
 */

// Build the collaboration service
const SuperDocCollaboration = new CollaborationBuilder()
  .withName('SuperDoc-Legal-Agent')
  .withDebounce(2000) // Auto-save every 2 seconds
  .withDocumentExpiryMs(30 * 60 * 1000) // 30 minute cache expiry

  .onConfigure((params) => {
    console.log('[Collab] Service configured');
  })

  .onAuthenticate(async ({ documentId, params, request }) => {
    // Token is passed in query params
    const token = params?.token;
    console.log(`[Auth] Authenticating token ${token} for document ${documentId}`);

    if (!token) {
      console.warn('[Auth] No token provided, using anonymous access');
      return {
        userId: 'anonymous',
        userEmail: 'anonymous@example.com',
        userName: 'Anonymous User',
      };
    }

    // Verify with FastAPI backend
    try {
      const response = await fetch(`${FASTAPI_URL}/api/documents/${documentId}/access?userId=${token}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        console.log(`[Auth] Access denied for user ${token} to document ${documentId}`);
        // Still allow but log the issue
        console.warn('[Auth] Backend denied access, allowing with warning');
        return {
          userId: token,
          userEmail: 'user@example.com',
          userName: 'User',
        };
      }

      const data = await response.json();
      console.log(`[Auth] User ${data.user_email} authenticated for document ${documentId}`);

      return {
        userId: token,
        userEmail: data.user_email,
        userName: data.user_email,
      };
    } catch (error) {
      // If FastAPI is not available, allow with warning
      console.warn(`[Auth] Could not verify with backend: ${error.message}`);
      console.warn('[Auth] Allowing connection without backend verification');
      return {
        userId: token,
        userEmail: 'user@example.com',
        userName: 'User',
      };
    }
  })

  .onLoad(async ({ documentId, userContext }) => {
    console.log(`[Load] Loading document: ${documentId}`);

    try {
      // Try to load existing Y.js state
      const stateResponse = await fetch(`${FASTAPI_URL}/api/documents/${documentId}/yjs-state`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (stateResponse.ok) {
        const data = await stateResponse.json();
        if (data.state && data.state.length > 10) {
          // Check if this is the marker string (not actual Y.js state)
          // The marker is base64 of 'COLLAB_ENABLED'
          if (data.state === 'Q09MTEJJX0VOQUJMRUQ=') {
            console.log(`[Load] Found collaboration marker for ${documentId}, initializing fresh`);
            console.log(`[Load] Creating empty Y.Doc for first client to initialize`);
            const emptyDoc = new Y.Doc();
            const emptyState = encodeStateAsUpdate(emptyDoc);
            console.log(`[Load] Returning empty Y.Doc state: ${emptyState.length} bytes`);
            return emptyState;
          }

          // Decode base64 state to Uint8Array
          const binaryString = atob(data.state);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          console.log(`[Load] Loaded existing Y.js state: ${bytes.length} bytes for document ${documentId}`);
          return bytes;
        }
      }

      // No saved state - return an empty Y.Doc
      // The client will initialize the meta map with its local DOCX data using isNewFile: true
      console.log(`[Load] No existing Y.js state for document ${documentId}`);
      console.log(`[Load] Creating empty Y.Doc for first client to initialize`);
      const emptyDoc = new Y.Doc();
      const emptyState = encodeStateAsUpdate(emptyDoc);
      console.log(`[Load] Returning empty Y.Doc state: ${emptyState.length} bytes`);
      return emptyState;
    } catch (error) {
      console.error(`[Load] Error loading document ${documentId}:`, error.message);
      return null;
    }
  })

  .onAutoSave(async (params) => {
    // Debug: log all params to see structure
    console.log(`[AutoSave] Received params:`, Object.keys(params));

    const documentId = params.documentId;
    const state = params.state || params.update;

    if (!state) {
      console.error(`[AutoSave] No state data received for ${documentId}`);
      return;
    }

    console.log(`[AutoSave] Saving document: ${documentId} (${state.length} bytes)`);

    try {
      // Convert Uint8Array to base64
      let binaryString = '';
      for (let i = 0; i < state.length; i++) {
        binaryString += String.fromCharCode(state[i]);
      }
      const base64State = btoa(binaryString);

      const response = await fetch(`${FASTAPI_URL}/api/documents/${documentId}/yjs-state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: base64State }),
      });

      if (response.ok) {
        console.log(`[AutoSave] Successfully saved document ${documentId}`);
      } else {
        console.error(`[AutoSave] Failed to save document ${documentId}: ${response.status}`);
      }
    } catch (error) {
      console.error(`[AutoSave] Error saving document ${documentId}:`, error.message);
    }
  })

  .onChange(({ documentId, userContext }) => {
    // Light operations only - this fires frequently
    // console.log(`[Change] Document ${documentId} changed`);
  })

  .build();

// WebSocket endpoint for collaboration
// SuperDoc connects directly to /:documentId (not /collaboration/:documentId)
fastify.register(async function (fastify) {
  fastify.get('/:documentId', { websocket: true }, (connection, request) => {
    const documentId = request.params.documentId;
    console.log(`[WS] New connection for document: ${documentId}`);

    // Extract token from query string - SuperDoc sends ?token=userId
    const url = new URL(request.url, `http://${request.headers.host}`);
    const token = url.searchParams.get('token');

    console.log(`[WS] Token from query: ${token}`);

    // Fastify v4 passes a connection object with socket property
    // Access the raw WebSocket from the connection
    const socket = connection.socket || connection;

    // Log socket properties
    console.log(`[WS] Socket type: ${socket.constructor.name}`);
    console.log(`[WS] Socket readyState: ${socket.readyState}`);
    console.log(`[WS] Socket has send: ${typeof socket.send}`);
    console.log(`[WS] Socket has on: ${typeof socket.on}`);

    // Add event listeners to track connection lifecycle
    socket.on('close', (code, reason) => {
      console.log(`[WS] Socket closed for ${documentId}: code=${code}`);
    });

    socket.on('error', (err) => {
      console.error(`[WS] Socket error for ${documentId}:`, err.message);
    });

    socket.on('message', (data) => {
      console.log(`[WS] Received message for ${documentId}: ${data.length} bytes`);
    });

    console.log(`[WS] Passing to SuperDocCollaboration.welcome()`);
    SuperDocCollaboration.welcome(socket, request).then(() => {
      console.log(`[WS] SuperDocCollaboration.welcome() completed for ${documentId}`);
    }).catch((err) => {
      console.error(`[WS] SuperDocCollaboration.welcome() error:`, err);
    });
  });
});

// Health check endpoint
fastify.get('/health', async (request, reply) => {
  return {
    status: 'healthy',
    service: 'SuperDoc Collaboration Server',
    timestamp: new Date().toISOString()
  };
});

// Start the server
const start = async () => {
  try {
    await fastify.listen({ port: PORT, host: '0.0.0.0' });
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   SuperDoc Collaboration Server                           ║
║   ─────────────────────────────────────────               ║
║                                                           ║
║   Status: Running                                         ║
║   Port: ${String(PORT).padEnd(47)}  ║
║   WebSocket URL: ws://localhost:${String(PORT).padEnd(26)} ║
║   FastAPI Backend: ${FASTAPI_URL.padEnd(35)}  ║
║                                                           ║
║   Ready for collaborative editing!                        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    `);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n[Server] Shutting down...');
  fastify.close().then(() => {
    console.log('[Server] Goodbye!');
    process.exit(0);
  });
});
