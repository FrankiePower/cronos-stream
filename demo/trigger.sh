#!/bin/bash

# A2A Agent Trigger Script
# Usage: ./trigger.sh [query]

# Default configuration
AGENT_URL="http://localhost:9001/rpc"
DISCOVERY_URL="http://localhost:8787"
QUERY="${1:-get premium content}" # Use first arg or default

echo "🚀 Triggering Paywall Agent..."
echo "   Agent: $AGENT_URL"
echo "   Discovery: $DISCOVERY_URL"
echo "   Query: \"$QUERY\""

# Python's uuid module is safer if uuidgen isn't present, but uuidgen is standard on Mac/Linux
UUID=$(uuidgen 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')

# JSON Payload Construction
# We use a variable to make the curl command cleaner
PAYLOAD=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "$UUID",
      "role": "user",
      "parts": [
        {
          "kind": "data",
          "data": {
            "discoveryUrls": ["$DISCOVERY_URL"],
            "query": "$QUERY"
          }
        }
      ]
    }
  },
  "id": 1
}
EOF
)

# Send Request
echo -e "\n📡 Sending JSON-RPC Request..."

RESPONSE=$(curl -s -X POST "$AGENT_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# Format Output
if command -v jq &> /dev/null; then
    echo -e "\n✅ Response (Formatted):"
    echo "$RESPONSE" | jq .
else
    echo -e "\n✅ Response (Raw - install 'jq' for formatting):"
    echo "$RESPONSE"
fi
