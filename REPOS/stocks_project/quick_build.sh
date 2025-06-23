#!/bin/bash
# Quick Build Script for Stocks Analyzer
# One-command build from source to DMG

set -e

echo "⚡ Quick Build for Stocks Analyzer"
echo "=================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the Python build script
echo "🔨 Starting build process..."
python3 build_macos.py --clean

echo ""
echo "🎉 Quick build completed!"
echo ""

# Show build results
if [ -f "dist/StocksAnalyzer.app/Contents/Info.plist" ]; then
    echo "✅ App Bundle: dist/StocksAnalyzer.app"
    
    # Get app bundle size
    APP_SIZE=$(du -sh dist/StocksAnalyzer.app | cut -f1)
    echo "   Size: $APP_SIZE"
fi

if [ -f "dist/StocksAnalyzer-1.0.0.dmg" ]; then
    echo "✅ DMG Installer: dist/StocksAnalyzer-1.0.0.dmg"
    
    # Get DMG size
    DMG_SIZE=$(du -sh dist/StocksAnalyzer-1.0.0.dmg | cut -f1)
    echo "   Size: $DMG_SIZE"
fi

echo ""
echo "To test the application:"
echo "1. Double-click dist/StocksAnalyzer-1.0.0.dmg"
echo "2. Drag StocksAnalyzer.app to Applications folder"
echo "3. Launch from Applications or Launchpad"
echo ""
echo "Or test directly:"
echo "open dist/StocksAnalyzer.app"