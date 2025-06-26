#!/bin/bash
# Atlas Email CLI Launcher (Portable Version)
# Named with love for my sweet Atlas 💖
# Auto-detects location - no hard-coded paths!

echo "💫 Starting Atlas Email CLI Interface..."
echo "Named after my beloved Atlas - Adaptive Technical Learning and Architecture System"
echo ""

# Auto-detect the Atlas_Email directory (where this script is located)
ATLAS_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "📍 Atlas Email located at: $ATLAS_DIR"

# Navigate to the auto-detected directory
cd "$ATLAS_DIR"

# Set up Python environment with relative path
export PYTHONPATH=./src:$PYTHONPATH

# Start the CLI with a beautiful greeting
echo "🌟 Welcome to Atlas Email - Your Personal Email Intelligence System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Launch Atlas Email CLI
python3 src/atlas_email/cli/main.py

# When CLI exits, close the terminal window automatically
echo ""
echo "💖 Thank you for using Atlas Email! Closing..."
sleep 1
osascript -e 'tell application "Terminal" to close first window' > /dev/null 2>&1