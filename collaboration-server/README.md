# SuperDoc Collaboration Server

HocusPocus-based real-time collaboration server for SuperDoc document editing.

## Features

- Real-time Y.js synchronization
- Document state persistence via FastAPI backend
- Authentication integration
- Multi-user awareness

## Setup

```bash
cd collaboration-server
npm install
```

## Configuration

Create a `.env` file:

```env
COLLAB_PORT=1234
FASTAPI_URL=http://localhost:8000
```

## Running

Development mode (with auto-reload):
```bash
npm run dev
```

Production mode:
```bash
npm start
```

## Architecture

The collaboration server:
1. Runs on port 1234 (configurable)
2. Handles WebSocket connections from SuperDoc clients
3. Syncs Y.js CRDT updates between clients
4. Persists document state to FastAPI backend (SQLite/PostgreSQL)
5. Authenticates users via FastAPI's document access API

## Integration

SuperDoc frontend connects to this server via WebSocket:
```javascript
modules: {
  collaboration: {
    url: 'ws://localhost:1234',
    token: 'user-id'
  }
}
```

The server communicates with FastAPI for:
- `/api/documents/{id}/yjs-state` - Get/Set Y.js state
- `/api/documents/{id}/access` - Verify user access
