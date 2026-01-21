#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}🛑 Stopping CronosStream Infrastructure...${NC}"

cd "$(dirname "$0")"

# 1. Stop Agent
if [ -f "agent.pid" ]; then
    PID=$(cat agent.pid)
    if ps -p $PID > /dev/null; then
        echo "Killing Agent Service (PID $PID)..."
        kill $PID
    else
        echo "Agent process $PID not found (already stopped?)"
    fi
    rm agent.pid
else
    # Fallback search
    PID=$(lsof -ti:9001 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Killing orphaned Agent Service (PID $PID)..."
        kill -9 "$PID"
    fi
fi
echo "✅ Agent Stopped."

# 2. Stop Docker
echo "Stopping Docker containers..."
docker compose down
echo "✅ Docker Stopped."

echo -e "${GREEN}Shutdown Complete.${NC}"
