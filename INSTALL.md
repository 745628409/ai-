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


## F. macOS 下 opencv-python wheel 构建失败时

如果出现 `Failed building wheel for opencv-python`，脚本会自动回退到 `requirements-macos-legacy.txt`（较老但更兼容的 OpenCV 版本）。

你也可以手工执行：

```bash
source .venv/bin/activate
pip install -r requirements-macos-legacy.txt pyinstaller
```
