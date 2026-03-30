#!/bin/bash
# Build Murmur.app for macOS and ad-hoc sign it.
# Usage: ./scripts/build_macos.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "==> Building Murmur.app..."

# Ensure venv
if [ ! -d ".venv" ]; then
    echo "No .venv found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Install pyinstaller if needed
.venv/bin/pip install pyinstaller -q

# Build
.venv/bin/pyinstaller \
    --name Murmur \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --osx-bundle-identifier com.murmur.dictation \
    --add-data "app:app" \
    --hidden-import AppKit \
    --hidden-import Quartz \
    --hidden-import Foundation \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import sounddevice \
    --hidden-import numpy \
    app/main.py

# Add LSUIElement to Info.plist (menu bar only, no dock icon)
PLIST="dist/Murmur.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Set :LSUIElement true" "$PLIST"

# Add microphone usage description
/usr/libexec/PlistBuddy -c "Add :NSMicrophoneUsageDescription string 'Murmur needs microphone access for voice dictation.'" "$PLIST" 2>/dev/null || true

echo "==> Ad-hoc signing..."
codesign --force --deep --sign - "dist/Murmur.app"

echo "==> Copying to /Applications..."
rm -rf /Applications/Murmur.app
cp -r dist/Murmur.app /Applications/

echo ""
echo "Done! Murmur.app installed to /Applications."
echo ""
echo "IMPORTANT: Add Murmur to Accessibility permissions:"
echo "  System Settings > Privacy & Security > Accessibility > '+' > Murmur"
echo ""
echo "Then launch Murmur from Applications or Spotlight."
