# 安装与打包（macOS 10.14）

## A. 用户安装（你拿到 dmg 后）
1. 双击 `ShotSearch.dmg`
2. 把 `ShotSearch.app` 拖入 `Applications`
3. 首次运行若弹出安全提示：
   - 系统偏好设置 -> 安全性与隐私 -> 仍要打开

## B. 开发者在 Mac 上生成 DMG

在项目根目录执行：

```bash
bash scripts/build_macos_dmg.sh
```

输出：

- `dist/ShotSearch.app`
- `ShotSearch.dmg`

> 说明：该脚本优先使用 `create-dmg`（如果已安装），否则回退到 `hdiutil` 生成基础安装镜像。

## C. 依赖说明

- Python 3.8~3.11（推荐 3.10）
- `requirements.txt`
- 打包工具：`pyinstaller`

## D. 签名与公证（正式分发建议）

如果你要给其他 Mac 用户“即装即用、无安全警告”体验，建议对 `.app` 和 `.dmg` 做 Apple Developer ID 签名与 notarization。


> 注意：Python 3.13 目前会在部分依赖安装阶段失败（如你遇到的 `setuptools.build_meta` / 构建后端错误），请改用 3.10 或 3.11。


## E. Windows 10 打包与运行

在 Windows PowerShell 中执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows_exe.ps1
```

或者双击/命令行执行：

```bat
scripts\build_windows_exe.bat
```

输出目录：

- `dist\ShotSearch\ShotSearch.exe`

把 `dist\ShotSearch` 整个目录打包成 zip 发给用户，解压后双击 `ShotSearch.exe` 即可运行（无需安装 Python）。


## F. macOS 下 opencv wheel 构建失败时

如果出现 `Failed building wheel for opencv-python` 或日志中出现 `nasm` / `CMake`，说明 pip 正在尝试源码编译。  
当前脚本已改为**仅安装二进制 wheel**并自动回退到 `requirements-macos-legacy.txt`（较老但更兼容的依赖组合），同时会轮询多个 `opencv-python` 版本寻找可用 wheel（包含部分 Mojave 上唯一可用但已 yanked 的历史版本）。
另外如果日志里显示“选中了 python3.10，但 `.venv` 仍是 python3.8”，请先删除旧虚拟环境再重试：

```bash
rm -rf .venv
bash scripts/build_macos_dmg.sh
```

你也可以手工执行：

```bash
source .venv/bin/activate
PIP_ONLY_BINARY=:all: pip install --prefer-binary -r requirements-macos-legacy.txt pyinstaller
PIP_ONLY_BINARY=:all: pip install --prefer-binary opencv-python==4.6.0.66
```

如果你在公司镜像源上始终拿不到 `opencv-python` 的 macOS wheel，可切换官方源：

```bash
PIP_INDEX_URL=https://pypi.org/simple bash scripts/build_macos_dmg.sh
```

如果出现 `THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE`，通常是系统级 `pip.conf` 开启了 `require-hashes` 或私有约束。  
新脚本已默认忽略系统 pip 配置；你也可以手工验证：

```bash
env -u PIP_REQUIRE_HASHES -u PIP_CONSTRAINT -u PIP_REQUIREMENT PIP_CONFIG_FILE=/dev/null pip install --upgrade pip
```

如果仍报同样 hash 错误，再清理缓存并禁用缓存安装：

```bash
pip cache purge
PIP_INDEX_URL=https://pypi.org/simple bash scripts/build_macos_dmg.sh
```
