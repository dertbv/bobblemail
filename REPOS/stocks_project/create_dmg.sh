#!/bin/bash
# DMG Creation Script for Stocks Analyzer
# Creates a professional DMG installer with custom background and layout

set -e  # Exit on any error

# Configuration
APP_NAME="StocksAnalyzer"
APP_VERSION="1.0.0"
DMG_NAME="${APP_NAME}-${APP_VERSION}"
BACKGROUND_IMAGE="dmg_background.png"
VOLUME_NAME="Stocks Analyzer"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
BUILD_DIR="${SCRIPT_DIR}/build"
DMG_DIR="${BUILD_DIR}/dmg"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
FINAL_DMG="${DIST_DIR}/${DMG_NAME}.dmg"

echo "Creating DMG installer for ${APP_NAME} v${APP_VERSION}"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: App bundle not found at $APP_PATH"
    echo "Please build the app first using build_macos.py"
    exit 1
fi

# Clean previous DMG builds
echo "Cleaning previous DMG builds..."
rm -rf "$DMG_DIR"
rm -f "$FINAL_DMG"
mkdir -p "$DMG_DIR"

# Copy app to DMG directory
echo "Copying app to DMG directory..."
cp -R "$APP_PATH" "$DMG_DIR/"

# Create Applications symlink
echo "Creating Applications symlink..."
ln -sf /Applications "$DMG_DIR/Applications"

# Create background image if it doesn't exist
if [ ! -f "${SCRIPT_DIR}/assets/${BACKGROUND_IMAGE}" ]; then
    echo "Creating DMG background image..."
    mkdir -p "${SCRIPT_DIR}/assets"
    
    # Create a simple background using Python
    python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

# Create background image
width, height = 600, 400
img = Image.new('RGB', (width, height), '#f0f0f0')
draw = ImageDraw.Draw(img)

# Add gradient background
for i in range(height):
    color = int(240 - (i * 20 / height))
    draw.line([(0, i), (width, i)], fill=(color, color, color))

# Add title
try:
    # Try to use a nice font
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
except:
    font = ImageFont.load_default()

title = 'Stocks Analyzer'
bbox = draw.textbbox((0, 0), title, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (width - text_width) // 2
y = 50

draw.text((x, y), title, fill='#333333', font=font)

# Add instruction text
try:
    font_small = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
except:
    font_small = ImageFont.load_default()

instruction = 'Drag the Stocks Analyzer app to Applications folder to install'
bbox = draw.textbbox((0, 0), instruction, font=font_small)
text_width = bbox[2] - bbox[0]
x = (width - text_width) // 2
y = height - 60

draw.text((x, y), instruction, fill='#666666', font=font_small)

# Save the image
img.save('${SCRIPT_DIR}/assets/${BACKGROUND_IMAGE}')
print('Background image created')
"
fi

# Create temporary DMG
echo "Creating temporary DMG..."
TEMP_DMG="${BUILD_DIR}/temp.dmg"
hdiutil create -srcfolder "$DMG_DIR" -volname "$VOLUME_NAME" -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" -format UDRW -size 200m "$TEMP_DMG"

# Mount the temporary DMG
echo "Mounting temporary DMG..."
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "$TEMP_DMG" | \
    egrep '^/dev/' | sed 1q | awk '{print $1}')
MOUNT_POINT="/Volumes/$VOLUME_NAME"

# Wait for mount
sleep 2

# Set up the DMG window appearance
echo "Setting up DMG appearance..."

# Copy background image to mounted volume
if [ -f "${SCRIPT_DIR}/assets/${BACKGROUND_IMAGE}" ]; then
    mkdir -p "$MOUNT_POINT/.background"
    cp "${SCRIPT_DIR}/assets/${BACKGROUND_IMAGE}" "$MOUNT_POINT/.background/"
fi

# Apply Finder view settings
osascript <<EOF
tell application "Finder"
    tell disk "$VOLUME_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 100, 1000, 500}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 96
        set background picture of viewOptions to file ".background:$BACKGROUND_IMAGE"
        
        -- Position the app icon
        set position of item "$APP_NAME.app" of container window to {150, 200}
        
        -- Position the Applications symlink
        set position of item "Applications" of container window to {450, 200}
        
        -- Update and close
        update without registering applications
        delay 2
        close
    end tell
end tell
EOF

# Make sure everything is written
sync

# Unmount the temporary DMG
echo "Unmounting temporary DMG..."
hdiutil detach "$DEVICE"

# Convert to final compressed DMG
echo "Creating final compressed DMG..."
hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$FINAL_DMG"

# Clean up
rm -f "$TEMP_DMG"
rm -rf "$DMG_DIR"

# Get file size
DMG_SIZE=$(du -h "$FINAL_DMG" | cut -f1)

echo "✅ DMG created successfully!"
echo "📦 File: $FINAL_DMG"
echo "📏 Size: $DMG_SIZE"
echo ""
echo "To test the DMG:"
echo "1. Double-click to mount: $FINAL_DMG"
echo "2. Drag $APP_NAME.app to Applications"
echo "3. Launch from Applications folder"