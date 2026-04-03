#!/usr/bin/env bash
set -euo pipefail

# macOS-only packaging helper
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[ERROR] 此脚本只能在 macOS 上运行。"
  exit 1
fi

APP_NAME="ShotSearch"
ENTRY="app/main.py"
ICON_PATH="packaging/AppIcon.icns"
DIST_DIR="dist"
BUILD_DIR="build"
DMG_NAME="${APP_NAME}.dmg"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

PYI_ARGS=(
  --name "$APP_NAME"
  --windowed
  --noconfirm
  --clean
  --add-data "app:app"
)

if [[ -f "$ICON_PATH" ]]; then
  PYI_ARGS+=(--icon "$ICON_PATH")
fi

pyinstaller "${PYI_ARGS[@]}" "$ENTRY"

APP_BUNDLE_PATH="$DIST_DIR/$APP_NAME.app"
if [[ ! -d "$APP_BUNDLE_PATH" ]]; then
  echo "[ERROR] 未找到 app bundle: $APP_BUNDLE_PATH"
  exit 1
fi

# 优先使用 create-dmg（可选），否则用 hdiutil 生成基础 dmg
if command -v create-dmg >/dev/null 2>&1; then
  rm -f "$DMG_NAME"
  create-dmg \
    --volname "$APP_NAME Installer" \
    --window-size 800 480 \
    --icon-size 100 \
    --icon "$APP_NAME.app" 220 240 \
    --hide-extension "$APP_NAME.app" \
    --app-drop-link 580 240 \
    "$DMG_NAME" \
    "$DIST_DIR"
else
  rm -f "$DMG_NAME"
  hdiutil create \
    -volname "$APP_NAME Installer" \
    -srcfolder "$DIST_DIR" \
    -ov \
    -format UDZO \
    "$DMG_NAME"
fi

echo "[OK] 生成完成: $(pwd)/$DMG_NAME"
