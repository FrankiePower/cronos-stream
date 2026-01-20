#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting CronosStream Universal Demo Setup...${NC}"

# Source env vars from sequencer and resource-service
# We map them to the names expected by docker-compose
if [ -f "../sequencer/.env" ]; then
    echo "Loading configuration from sequencer/.env..."
    export SEQUENCER_PRIVATE_KEY=$(grep SEQUENCER_PRIVATE_KEY ../sequencer/.env | cut -d '=' -f2)
    export CHANNEL_MANAGER_ADDRESS=$(grep CHANNEL_MANAGER_ADDRESS ../sequencer/.env | cut -d '=' -f2)
else
    echo "Error: ../sequencer/.env not found."
    exit 1
fi

if [ -f "../a2a/resource-service/.env" ]; then
    echo "Loading configuration from a2a/resource-service/.env..."
    export MERCHANT_ADDRESS=$(grep MERCHANT_ADDRESS ../a2a/resource-service/.env | cut -d '=' -f2)
fi

echo -e "${GREEN}Configuration:${NC}"
echo "CHANNEL_MANAGER_ADDRESS: $CHANNEL_MANAGER_ADDRESS"
echo "MERCHANT_ADDRESS: $MERCHANT_ADDRESS"

# Start Docker containers
echo -e "${GREEN}Bringing up Docker containers...${NC}"
docker compose up -d --build

# Wait for services
echo -e "${GREEN}Waiting for services to be healthy...${NC}"
echo "Waiting for Sequencer (localhost:4001)..."
until curl -s http://localhost:4001/health > /dev/null; do
    sleep 2
    printf "."
done
echo " Sequencer is up!"

echo "Waiting for Resource Service (localhost:8787)..."
until curl -s http://localhost:8787/health > /dev/null; do
    sleep 2
    printf "."
done
echo " Resource Service is up!"

echo -e "${GREEN}Universal Setup is ready!${NC}"
echo "Sequencer: http://localhost:4001"
echo "Resource Service: http://localhost:8787"
echo ""
echo "To stop: docker compose down"
