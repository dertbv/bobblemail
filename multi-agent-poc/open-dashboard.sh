#!/bin/bash

# Open the monitoring dashboard

echo "🎭 Opening Multi-Agent Communication Monitor..."
echo ""
echo "Dashboard will open in your default browser."
echo "Make sure the message broker is running at http://localhost:3000"
echo ""

# Open in default browser
open monitor-dashboard.html

echo "Dashboard opened!"
echo ""
echo "Quick commands:"
echo "  Check broker: curl http://localhost:3000/status | jq"
echo "  View agents:  tmux list-sessions | grep claudesquad"
echo "  Broker logs:  tmux attach -t message-broker"