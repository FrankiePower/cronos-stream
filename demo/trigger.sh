#!/bin/bash
echo "Triggering Agent to fetch paywalled resource..."
# Generate a random UUID for messageId
uuid=$(uuidgen || echo "12345678-1234-5678-1234-567812345678")

curl -X POST http://localhost:9001/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "'"$uuid"'",
        "role": "user",
        "parts": [
          {
            "kind": "data",
            "data": {
                "discoveryUrls": ["http://localhost:8787"],
                "query": "get paywalled resource"
            }
          }
        ]
      }
    },
    "id": 1
  }'
echo -e "\nRequest sent!"
