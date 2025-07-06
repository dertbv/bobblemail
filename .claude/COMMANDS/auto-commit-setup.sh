#!/bin/bash

# Setup script for auto-commit system

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AUTO_COMMIT_SCRIPT="$SCRIPT_DIR/auto-commit.sh"

echo "🚀 Setting up ATLAS Auto-Commit System"

# Make script executable
chmod +x "$AUTO_COMMIT_SCRIPT"

# Option 1: LaunchAgent (macOS) - Recommended
setup_launchagent() {
    echo "Setting up LaunchAgent for automatic startup..."
    
    PLIST_FILE="$HOME/Library/LaunchAgents/com.atlas.autocommit.plist"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.atlas.autocommit</string>
    <key>ProgramArguments</key>
    <array>
        <string>$AUTO_COMMIT_SCRIPT</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PWD</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/.auto-commit.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.auto-commit-error.log</string>
</dict>
</plist>
EOF

    # Load the agent
    launchctl load "$PLIST_FILE"
    echo "✅ LaunchAgent installed and started"
    echo "   Auto-commit will run on system startup"
}

# Option 2: Git Hook
setup_git_hook() {
    echo "Setting up git post-commit hook..."
    
    HOOK_FILE=".git/hooks/post-commit"
    
    cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash
# Check if it's been 30+ minutes since last auto-commit
LAST_COMMIT_FILE="/tmp/.last_auto_commit_$(pwd | md5)"
INTERVAL=1800  # 30 minutes

if [ -f "$LAST_COMMIT_FILE" ]; then
    last_time=$(cat "$LAST_COMMIT_FILE")
    current_time=$(date +%s)
    diff=$((current_time - last_time))
    
    if [ $diff -ge $INTERVAL ]; then
        # Run auto-commit in background
        (cd "$(git rev-parse --show-toplevel)" && ./.claude/COMMANDS/auto-commit.sh --once &)
        echo "$current_time" > "$LAST_COMMIT_FILE"
    fi
else
    echo "$(date +%s)" > "$LAST_COMMIT_FILE"
fi
EOF

    chmod +x "$HOOK_FILE"
    echo "✅ Git hook installed"
}

# Option 3: Simple background process
setup_background() {
    echo "Starting auto-commit as background process..."
    nohup "$AUTO_COMMIT_SCRIPT" > /dev/null 2>&1 &
    echo $! > "$HOME/.auto-commit.pid"
    echo "✅ Background process started (PID: $(cat $HOME/.auto-commit.pid))"
    echo "   To stop: kill $(cat $HOME/.auto-commit.pid)"
}

# Menu
echo ""
echo "Choose setup method:"
echo "1) LaunchAgent (recommended - survives reboot)"
echo "2) Git Hook (triggers on manual commits)"
echo "3) Background Process (simple, current session only)"
echo "4) Manual only (run './auto-commit.sh --once' when needed)"
echo ""
read -p "Selection (1-4): " choice

case $choice in
    1)
        setup_launchagent
        ;;
    2)
        setup_git_hook
        ;;
    3)
        setup_background
        ;;
    4)
        echo "✅ Manual mode configured"
        echo "   Run: $AUTO_COMMIT_SCRIPT --once"
        ;;
    *)
        echo "Invalid selection"
        exit 1
        ;;
esac

echo ""
echo "🎉 Auto-commit system ready!"
echo ""
echo "Features:"
echo "- Commits every 30 minutes if changes exist"
echo "- Pushes every 60 minutes to avoid conflicts"
echo "- Smart commit messages based on changes"
echo "- Skips during merge/rebase operations"
echo "- Logs to ~/.auto-commit.log"
echo ""
echo "Manual commands:"
echo "- Run once: $AUTO_COMMIT_SCRIPT --once"
echo "- Check log: tail -f ~/.auto-commit.log"
echo "- Stop daemon: launchctl unload ~/Library/LaunchAgents/com.atlas.autocommit.plist"