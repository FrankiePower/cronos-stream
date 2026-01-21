#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=================================================="
echo -e "🚀 CronosStream Performance Benchmark"
echo -e "==================================================${NC}"

# Explanation
echo -e "\n${BLUE}ℹ️  What this does:${NC}"
echo "   1. Connects to the CronosStream Sequencer."
echo "   2. Synchronizes channel state (Sequence Numbers, Nonces)."
echo "   3. Floods the Sequencer with signed vouchers (simulate high-traffic)."
echo "   4. Measures:"
echo "      - Throughput (TPS)"
echo "      - Latency (ms)"
echo "      - Success Rate"

echo -e "\n${BLUE}📋 Methodology:${NC}"
echo "   We run two distinct tests:"
echo "   A. Live Signing: Real-time EIP-712 signing per request (CPU intensive)."
echo "   B. Pre-Signed:   Replaying valid vouchers (Network/IO intensive)."

echo -e "\n${BLUE}⏳ Starting Benchmark Suite...${NC}"
echo "   (This may take 30-60 seconds)"
echo "--------------------------------------------------"

# Ensure dependencies
cd "$(dirname "$0")"
if [ ! -d "../a2a/a2a-service/venv" ]; then
    echo "Creating virtual environment..."
    cd "../a2a/a2a-service"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    cd ../../demo
else
    source ../a2a/a2a-service/venv/bin/activate
fi

# Run the python suite
python3 ../scripts/benchmark_suite.py

echo -e "\n${GREEN}=================================================="
echo -e "✅ Benchmark Complete"
echo -e "==================================================${NC}"
echo "Metrics have been logged above."
