# Stocks Analyzer - macOS Standalone Application Build Guide

This guide explains how to package the Stocks Analyzer web application into a standalone macOS application that can run on any Mac without requiring Python or dependencies to be installed.

## Overview

The build system creates:
- **StocksAnalyzer.app** - Native macOS application bundle
- **StocksAnalyzer-1.0.0.dmg** - Professional installer package

The packaged application includes:
- Python interpreter and all dependencies
- Flask web server with automatic port management
- All templates, static files, and data structures
- Browser auto-launch functionality
- Native macOS integration (dock icon, notifications)

## Quick Start

### Option 1: One-Command Build

```bash
# Setup environment and build in one go
./setup_build_environment.sh && ./quick_build.sh
```

### Option 2: Step-by-Step Build

```bash
# 1. Setup build environment
./setup_build_environment.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Build the application
python3 build_macos.py --clean
```

## Build Requirements

### System Requirements
- macOS 10.13 (High Sierra) or later
- 4GB free disk space
- Internet connection for downloading dependencies

### Required Tools
- Python 3.8+ (automatically installed via Homebrew)
- Homebrew package manager
- Xcode Command Line Tools

The setup script will automatically install missing dependencies.

## Build Process Details

### Phase 1: Environment Setup
- Installs Homebrew if missing
- Creates Python virtual environment
- Installs all Python dependencies
- Verifies all components can import successfully

### Phase 2: Asset Creation
- Generates application icon (stocks chart design)
- Creates necessary build directories
- Prepares static resources

### Phase 3: PyInstaller Build
- Analyzes Python dependencies
- Bundles Flask app with all modules
- Creates macOS app bundle with proper structure
- Includes templates, static files, and data directories

### Phase 4: DMG Creation
- Creates professional installer with custom background
- Adds Applications folder symlink
- Optimizes for easy drag-and-drop installation
- Compresses for smaller download size

## Build Files Explained

| File | Purpose |
|------|---------|
| `stocks_launcher.py` | Main entry point that manages Flask server and browser |
| `stocks.spec` | PyInstaller configuration with all dependencies |
| `build_macos.py` | Complete build automation script |
| `setup_build_environment.sh` | Environment setup and dependency installation |
| `quick_build.sh` | One-command build script |
| `create_dmg.sh` | DMG installer creation script |
| `requirements_build.txt` | Build-specific Python dependencies |

## Troubleshooting

### Common Build Issues

#### 1. Python Version Error
```
❌ Python 3.8 or higher is required
```
**Solution:** Install Python 3.11+ via Homebrew:
```bash
brew install python@3.11
```

#### 2. Missing Dependencies
```
❌ Failed to import: ['pandas', 'yfinance']
```
**Solution:** Reinstall dependencies:
```bash
source venv/bin/activate
pip install -r requirements_build.txt
```

#### 3. PyInstaller Import Errors
```
ModuleNotFoundError: No module named 'some_module'
```
**Solution:** Add the module to `hiddenimports` in `stocks.spec`

#### 4. DMG Creation Fails
```
hdiutil: create failed - Resource busy
```
**Solution:** Make sure no existing DMG is mounted:
```bash
hdiutil detach /Volumes/StocksAnalyzer
```

### Build Artifacts

After successful build, you'll find:

```
dist/
├── StocksAnalyzer.app/          # Main application bundle
│   ├── Contents/
│   │   ├── Info.plist          # App metadata
│   │   ├── MacOS/
│   │   │   └── stocks_launcher # Main executable
│   │   └── Resources/          # Templates, static files
│   └── ...
├── StocksAnalyzer-1.0.0.dmg    # Installer package
└── build_info.json             # Build metadata
```

## Testing the Application

### Quick Test
```bash
# Test the app bundle directly
open dist/StocksAnalyzer.app
```

### Full Installation Test
```bash
# Mount the DMG
open dist/StocksAnalyzer-1.0.0.dmg

# Drag app to Applications folder
# Launch from Applications folder or Launchpad
```

### Expected Behavior
1. App launches without showing terminal
2. Browser opens automatically to http://127.0.0.1:5000
3. All web interface functionality works
4. Data is saved to `~/Documents/StocksAnalyzer/`
5. App appears in Dock with custom icon
6. macOS notifications work properly

## Customization

### Changing App Icon
1. Replace `assets/icon.icns` with your custom icon
2. Rebuild the application

### Modifying DMG Appearance
1. Edit `create_dmg.sh` background image creation
2. Adjust window size and icon positions
3. Rebuild DMG only: `./create_dmg.sh`

### App Metadata
Edit the `info_plist` section in `stocks.spec`:
```python
info_plist={
    'CFBundleName': 'Your App Name',
    'CFBundleDisplayName': 'Display Name',
    'CFBundleVersion': '2.0.0',
    # ... other properties
}
```

## Distribution

### For Personal Use
The generated DMG can be shared directly:
- File size: ~50-100MB (depending on dependencies)
- No code signing required for personal use
- Works on macOS 10.13+

### For Public Distribution
For broader distribution, consider:

1. **Code Signing** (requires Apple Developer account)
```bash
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/StocksAnalyzer.app
```

2. **Notarization** (for Gatekeeper compatibility)
```bash
xcrun notarytool submit dist/StocksAnalyzer-1.0.0.dmg --keychain-profile "AC_PASSWORD" --wait
```

3. **Automated Updates** (consider using Sparkle framework)

## Performance Considerations

### App Bundle Size
- Typical size: 80-120MB
- Includes complete Python runtime
- All scientific computing libraries (NumPy, Pandas, Matplotlib)

### Startup Time
- Cold start: 3-5 seconds
- Warm start: 1-2 seconds
- Flask server ready: 2-3 seconds after launch

### Memory Usage
- Base app: ~50-80MB RAM
- During analysis: 200-500MB RAM (depending on data size)
- Releases memory after analysis completion

## Maintenance

### Updating Dependencies
1. Update `requirements.txt` and `requirements_build.txt`
2. Rebuild with `--clean` flag
3. Test thoroughly before distribution

### Version Management
1. Update version in `build_macos.py`
2. Update `CFBundleVersion` in `stocks.spec`
3. Rebuild and test

### Monitoring Issues
- Check `~/Documents/StocksAnalyzer/app.log` for runtime issues
- Use Console.app to view system logs
- Test on different macOS versions

## Support

For build issues:
1. Check this README and troubleshooting section
2. Verify all requirements are met
3. Try clean build: `python3 build_macos.py --clean`
4. Check system logs in Console.app

The build system is designed to be robust and self-contained, but complex applications can have edge cases. The modular design allows for easy debugging and customization of specific components.