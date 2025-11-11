#!/bin/bash

# Start script for User-to-User Negotiation System

echo "=========================================="
echo "   User-to-User Negotiation System"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Backend already running on port 8000${NC}"
else
    echo -e "${BLUE}Starting Backend...${NC}"
    cd "$(dirname "$0")"
    python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"
    sleep 2
fi

# Check if frontend is already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Frontend already running on port 3000${NC}"
else
    echo -e "${BLUE}Starting Frontend...${NC}"
    cd frontend

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing dependencies...${NC}"
        npm install
    fi

    npm run dev &
    FRONTEND_PID=$!
    echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "   System Started Successfully!"
echo "==========================================${NC}"
echo ""
echo -e "Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "Frontend: ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}Testing Instructions:${NC}"
echo "1. Open http://localhost:3000 in two browsers"
echo "2. Register two users from different companies"
echo "3. User A: Create negotiation → Enter User B email"
echo "4. User B: Accept negotiation"
echo "5. Both: Chat in real-time!"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for Ctrl+C
wait
