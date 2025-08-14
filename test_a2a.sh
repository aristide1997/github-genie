#!/bin/bash

# Test script for GitHub Genie A2A server
# Usage: ./test_a2a.sh

echo "=== GitHub Genie A2A Server Test ==="
curl -sS -N -X POST http://localhost:8000/ \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": "req-1",
    "method": "message/stream",
    "params": {
      "message": {
        "messageId": "msg-12345",
        "role": "user",
        "parts": [
          { "kind": "text", "text": "tell me what type of agents you have in llamaindex https://github.com/run-llama/llama_index.git" }
        ]
      }
    }
  }' | cat -v
