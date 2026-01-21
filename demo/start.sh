#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting CronosStream Demo Suite...${NC}"

# ==============================================================================
# 1. Environment & Config
# ==============================================================================
cd "$(dirname "$0")"

# Source env vars
if [ -f "../sequencer/.env" ]; then
    echo "Loading configuration from sequencer/.env..."
    export SEQUENCER_PRIVATE_KEY=$(grep SEQUENCER_PRIVATE_KEY ../sequencer/.env | cut -d '=' -f2)
    export CHANNEL_MANAGER_ADDRESS=$(grep CHANNEL_MANAGER_ADDRESS ../sequencer/.env | cut -d '=' -f2)
else
    echo -e "${RED}Error: ../sequencer/.env not found.${NC}"
    exit 1
fi

if [ -f "../a2a/resource-service/.env" ]; then
    echo "Loading configuration from a2a/resource-service/.env..."
    export MERCHANT_ADDRESS=$(grep MERCHANT_ADDRESS ../a2a/resource-service/.env | cut -d '=' -f2)
fi

# ==============================================================================
# 2. Start Infrastructure (Docker)
# ==============================================================================
echo -e "${BLUE}🐳 Docker: Starting containers...${NC}"
docker compose up -d --build

echo "Waiting for services to be healthy..."
until curl -s http://localhost:4001/health > /dev/null; do
    sleep 2
    printf "."
done
echo -e "\n✅ Sequencer is UP"

until curl -s http://localhost:8787/health > /dev/null; do
    sleep 2
    printf "."
done
echo -e "✅ Resource Service is UP"

# ==============================================================================
# 3. Start Agent Service (Python Background)
# ==============================================================================
echo -e "${BLUE}🤖 Agent: Booting AI Service...${NC}"

# Setup Python Env
cd ../a2a/a2a-service
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
else
    source venv/bin/activate
fi

# Kill old process if exists
PID=$(lsof -ti:9001 2>/dev/null || true)
if [ -n "$PID" ]; then
    echo "Killing existing agent (PID $PID)..."
    kill -9 "$PID"
fi

# Start in background
nohup python3 -m host.main > ../../demo/agent.log 2>&1 &
AGENT_PID=$!
echo "$AGENT_PID" > ../../demo/agent.pid

echo -e "✅ Agent Service started (PID $AGENT_PID)"
echo -e "   Logs: demo/agent.log"

# ==============================================================================
# 4. Ready
# ==============================================================================
echo -e "\n${GREEN}✨ SYSTEM READY ✨${NC}"
echo "--------------------------------------------------------"
echo "1. Run the Demo:      ./agent.sh \"I want premium content\""
echo "2. Stop Everything:   ./stop.sh"
echo "--------------------------------------------------------"
