#!/usr/bin/env bash
set -euo pipefail

# macOS-only packaging helper
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[ERROR] 此脚本只能在 macOS 上运行。"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

APP_NAME="ShotSearch"
ENTRY="$ROOT_DIR/app/main.py"
ICON_PATH="$ROOT_DIR/packaging/AppIcon.icns"
DIST_DIR="$ROOT_DIR/dist"
DMG_NAME="$ROOT_DIR/${APP_NAME}.dmg"
REQ_FILE="$ROOT_DIR/requirements.txt"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "[ERROR] 未找到 requirements.txt: $REQ_FILE"
  exit 1
fi

python3 -m venv "$ROOT_DIR/.venv"
source "$ROOT_DIR/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$REQ_FILE" pyinstaller

PYI_ARGS=(
  --name "$APP_NAME"
  --windowed
  --noconfirm
  --clean
  --add-data "$ROOT_DIR/app:app"
  --distpath "$DIST_DIR"
  --workpath "$ROOT_DIR/build"
  --specpath "$ROOT_DIR"
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

echo "[OK] 生成完成: $DMG_NAME"
