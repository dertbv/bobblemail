#!/bin/bash

# Atlas Email Launcher Script
echo "🌟 Starting Atlas Email..."

# Navigate to project directory
cd "/Users/Badman/Desktop/email/REPOS/Atlas_Email"

# Function to check if port 8001 is in use
check_port() {
    lsof -i :8001 >/dev/null 2>&1
}

# Start web app if not already running
if ! check_port; then
    echo "🌐 Starting web interface..."
    PYTHONPATH=src python3 -m atlas_email.api.app &
    sleep 3
    echo "✅ Web interface started at http://localhost:8001"
else
    echo "✅ Web interface already running at http://localhost:8001"
fi

# Open web browser
echo "🌐 Opening web browser..."
open "http://localhost:8001"

# Ask if user wants CLI too
echo ""
echo "Would you like to open the CLI interface too? (y/n)"
read -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "💻 Opening CLI interface..."
    osascript -e 'tell application "Terminal" to do script "cd \"/Users/Badman/Desktop/email/REPOS/Atlas_Email\" && PYTHONPATH=src python3 -m atlas_email.cli.main"'
fi

echo "✅ Atlas Email launched successfully!"
echo "🌐 Web: http://localhost:8001"
echo "💻 CLI available in Terminal"
