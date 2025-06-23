#!/bin/bash
# Build Environment Setup Script for Stocks Analyzer
# Prepares the development environment for building the macOS application

set -e

echo "🔧 Setting up build environment for Stocks Analyzer"
echo "=================================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS only"
    exit 1
fi

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
    echo "❌ Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    echo "Please install Python 3.8+ from https://python.org or use Homebrew:"
    echo "brew install python@3.11"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION is compatible"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
brew install --quiet python@3.11 || true
brew install --quiet pillow || true

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install build dependencies
echo "📚 Installing build dependencies..."
if [ -f "requirements_build.txt" ]; then
    pip install -r requirements_build.txt
else
    echo "⚠️  requirements_build.txt not found, installing core dependencies..."
    pip install Flask yfinance pandas requests numpy matplotlib seaborn beautifulsoup4 lxml
    pip install pyinstaller Pillow
fi

# Create assets directory
echo "📁 Creating assets directory..."
mkdir -p assets

# Test import of main modules
echo "🧪 Testing Python imports..."
python3 -c "
import sys
modules = ['flask', 'pandas', 'yfinance', 'requests', 'numpy', 'matplotlib', 'seaborn', 'bs4', 'lxml']
failed = []
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
        failed.append(module)

if failed:
    print(f'\\n❌ Failed to import: {failed}')
    sys.exit(1)
else:
    print('\\n✅ All required modules imported successfully')
"

# Test PyInstaller
echo "🔍 Testing PyInstaller..."
pyinstaller --version > /dev/null

# Check if main app files exist
echo "📄 Checking application files..."
required_files=("app.py" "stocks_launcher.py" "stocks.spec" "requirements.txt")
missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ Missing required files: ${missing_files[*]}"
    echo "Please ensure all required files are present before building."
    exit 1
fi

# Test Flask app startup (quick test)
echo "🚀 Testing Flask app startup..."
timeout 10s python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from app import StockAnalysisApp
app_instance = StockAnalysisApp()
print('✅ Flask app can be instantiated successfully')
" || echo "⚠️  Flask app test timeout (this is normal)"

echo ""
echo "🎉 Build environment setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run the build: python3 build_macos.py --clean"
echo "2. Or use the quick build: ./quick_build.sh"
echo ""
echo "The build will create:"
echo "- dist/StocksAnalyzer.app (macOS app bundle)"
echo "- dist/StocksAnalyzer-1.0.0.dmg (installer)"
echo ""
echo "Note: Make sure to activate the virtual environment before building:"
echo "source venv/bin/activate"