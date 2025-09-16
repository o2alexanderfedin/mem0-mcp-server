#!/bin/bash

echo "Testing graph relationship creation via REST API..."

curl -X POST http://localhost:8765/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Sarah Johnson is the CTO of AI Hive and works closely with Alexander on the technical architecture"},
      {"role": "assistant", "content": "Noted that Sarah Johnson is the CTO of AI Hive working with Alexander on technical architecture"}
    ],
    "user_id": "alexander_fedin",
    "metadata": {"source": "team_info"}
  }'

echo ""
echo ""
echo "Retrieving all memories to check for graph relationships..."

curl -s "http://localhost:8765/memories?user_id=alexander_fedin" | python3 -m json.tool