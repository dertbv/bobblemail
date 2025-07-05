#!/bin/bash

# Send task to stooges

curl -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "agent_id": "director",
  "description": "ATTENTION STOOGES: New project assignment!",
  "content": {
    "project": "Build a Comedy Spam Filter",
    "details": "Create a spam filter that detects ridiculous spam emails",
    "assignments": {
      "mo": "Design detection rules for silly spam patterns",
      "larry": "Implement the filter code (bugs expected)",
      "curly": "Create test spam emails (the sillier the better)"
    },
    "examples": [
      "Congratulations! You've won a lifetime supply of rubber chickens",
      "Hot singles in your area want to discuss quantum physics",
      "Nigerian astronaut stuck in space needs $5000 to return"
    ]
  },
  "tags": ["task", "project", "stooge", "spam-filter"]
}
EOF

echo "Task sent to the stooges!"