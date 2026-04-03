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
LEGACY_REQ_FILE="$ROOT_DIR/requirements-macos-legacy.txt"

pick_python() {
  for bin in python3.10 python3.11 python3.9 python3.8 python3; do
    if command -v "$bin" >/dev/null 2>&1; then
      echo "$bin"
      return 0
    fi
  done
  return 1
}

PY_BIN="$(pick_python || true)"
if [[ -z "$PY_BIN" ]]; then
  echo "[ERROR] 未找到可用 Python。请安装 Python 3.8~3.11（推荐 3.10）。"
  exit 1
fi

PY_VER="$($PY_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MINOR="$($PY_BIN -c 'import sys; print(sys.version_info.minor)')"
if [[ "$PY_MINOR" -lt 8 || "$PY_MINOR" -gt 11 ]]; then
  echo "[ERROR] 当前 Python=$PY_VER，不受支持。请使用 Python 3.8~3.11（推荐 3.10）。"
  exit 1
fi

echo "[INFO] 使用 Python: $PY_BIN ($PY_VER)"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "[ERROR] 未找到 requirements.txt: $REQ_FILE"
  exit 1
fi

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  VENV_VER="$("$ROOT_DIR/.venv/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
  if [[ -n "$VENV_VER" && "$VENV_VER" != "$PY_VER" ]]; then
    echo "[WARN] 检测到已有 .venv 使用 Python $VENV_VER，与当前选择 $PY_VER 不一致，正在重建 .venv..."
    rm -rf "$ROOT_DIR/.venv"
  fi
fi

"$PY_BIN" -m venv "$ROOT_DIR/.venv"
source "$ROOT_DIR/.venv/bin/activate"

pip_safe() {
  PIP_CONFIG_FILE=/dev/null PIP_REQUIRE_HASHES=0 python -m pip "$@"
}

pip_safe install --upgrade pip setuptools wheel

install_with_binary_wheels() {
  local req_path="$1"
  PIP_CONFIG_FILE=/dev/null PIP_REQUIRE_HASHES=0 PIP_ONLY_BINARY=:all: \
    python -m pip install --prefer-binary -r "$req_path" pyinstaller
}

install_opencv_binary() {
  local -a candidates=(
    "opencv-python==4.7.0.68"
    "opencv-python==4.6.0.66"
    "opencv-python==4.5.5.64"
    "opencv-python==4.5.3.56"
    "opencv-python==4.1.2.30"
  )
  for pkg in "${candidates[@]}"; do
    echo "[INFO] 尝试安装 OpenCV 二进制包: $pkg"
    if PIP_CONFIG_FILE=/dev/null PIP_REQUIRE_HASHES=0 PIP_ONLY_BINARY=:all: \
      python -m pip install --prefer-binary "$pkg"; then
      return 0
    fi
  done
  return 1
}

install_stack() {
  local req_path="$1"
  install_with_binary_wheels "$req_path" && install_opencv_binary
}

if ! install_stack "$REQ_FILE"; then
  echo "[WARN] 主依赖安装失败，尝试 macOS 兼容降级依赖..."
  if [[ ! -f "$LEGACY_REQ_FILE" ]]; then
    echo "[ERROR] 未找到降级依赖文件: $LEGACY_REQ_FILE"
    exit 1
  fi
  if ! install_stack "$LEGACY_REQ_FILE"; then
    cat <<'EOF'
[ERROR] 仍未能安装二进制依赖（已避免源码编译）。
可能原因：
  1) 当前 venv 的 Python 版本或 CPU 架构没有可用 wheel。
  2) pip 版本过旧或网络镜像缺少对应 wheel。
  3) 当前镜像源缺少 macOS 对应的 opencv-python wheel。
  4) 系统 pip 配置启用了 hash 校验或私有约束，导致第三方包被拒绝。

建议：
  - 使用 Python 3.10（Intel x86_64）后重试；
  - 删除 .venv 后重试（避免沿用旧 Python 版本）；
  - 临时切换官方 PyPI 源后重试：
      PIP_INDEX_URL=https://pypi.org/simple bash scripts/build_macos_dmg.sh
  - 若日志出现 nasm / CMake，说明触发了源码构建，本脚本已阻止该路径。
EOF
    exit 1
  fi
fi

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
