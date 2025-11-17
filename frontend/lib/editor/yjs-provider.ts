/**
 * Yjs provider configuration for real-time collaboration.
 *
 * This module sets up WebSocket and IndexedDB providers for collaborative editing:
 * - WebSocketProvider: Syncs document state across multiple clients in real-time
 * - IndexeddbPersistence: Stores document locally for offline access
 */

import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";
import { IndexeddbPersistence } from "y-indexeddb";

// Get WebSocket URL from environment or default to localhost
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export interface YjsProviderConfig {
  documentId: string;
  userId: string;
  userName: string;
  userColor: string;
}

export interface YjsProviders {
  doc: Y.Doc;
  provider: WebsocketProvider;
  indexeddbProvider: IndexeddbPersistence;
}

/**
 * Initialize Yjs providers for a document.
 *
 * @param config - Configuration for the providers
 * @returns Yjs document and providers
 */
export function createYjsProviders(config: YjsProviderConfig): YjsProviders {
  const { documentId, userId, userName, userColor } = config;

  // Create Yjs document
  const doc = new Y.Doc();

  // TEMPORARILY DISABLED: IndexedDB persistence causing decoding errors
  // Will re-enable after ensuring WebSocket sync works properly
  // const indexeddbProvider = new IndexeddbPersistence(documentId, doc);
  const indexeddbProvider = null as any; // Placeholder

  // // Handle IndexedDB errors (corrupted data)
  // indexeddbProvider.on("synced", () => {
  //   console.log("[Yjs] IndexedDB synced successfully");
  // });

  // Set up WebSocket provider for real-time sync
  // Note: y-websocket appends the room name to the URL, so we configure
  // the base URL to be ws://localhost:8000/ws/documents and use documentId as room
  const provider = new WebsocketProvider(
    `${WS_URL}/ws/documents`,
    documentId,
    doc,
    {
      // Authentication token will be sent via query params
      params: {
        userId,
      },
    }
  );

  // Set user awareness information (for cursors and presence)
  provider.awareness.setLocalStateField("user", {
    id: userId,
    name: userName,
    color: userColor,
  });

  // Log connection status
  provider.on("status", (event: { status: string }) => {
    console.log(`[Yjs] WebSocket status: ${event.status}`);
  });

  provider.on("sync", (isSynced: boolean) => {
    console.log(`[Yjs] Document synced: ${isSynced}`);
  });

  return {
    doc,
    provider,
    indexeddbProvider,
  };
}

/**
 * Clean up Yjs providers when component unmounts.
 *
 * @param providers - Providers to destroy
 */
export function destroyYjsProviders(providers: YjsProviders): void {
  providers.provider.destroy();
  // IndexedDB temporarily disabled
  // providers.indexeddbProvider?.destroy();
}
