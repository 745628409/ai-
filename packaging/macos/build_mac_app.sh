#!/usr/bin/env bash
set -e

# 适配 macOS 10.14：建议使用 Python 3.9
# 检查 python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3，请先安装 Python 3.9（推荐）"
  exit 1
fi

python3 -m venv .venv-pack
source .venv-pack/bin/activate

python -m pip install --upgrade pip
pip install -r backend/requirements.txt
pip install pyinstaller==5.13.2

# macOS 下 --add-data 使用冒号分隔
pyinstaller \
  --noconfirm \
  --windowed \
  --name "Novel2Screen" \
  --add-data "backend:backend" \
  run.py

cat > dist/双击运行.command <<'CMD'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
open "$DIR/Novel2Screen.app"
CMD
chmod +x dist/双击运行.command

echo "打包完成：dist/Novel2Screen.app"
echo "双击 dist/双击运行.command 即可打开应用"
