# macOS 10.14 即用打包说明

## 目标
为 macOS 10.14 用户提供“可双击打开”的 `.app`。

## 前置要求（只需一次）
1. 安装 Python 3.9（推荐）
2. 打开终端进入项目目录

## 一键打包
```bash
./packaging/macos/build_mac_app.sh
```

完成后会生成：
- `dist/Novel2Screen.app`
- `dist/双击运行.command`

你可以直接双击 `dist/双击运行.command` 打开应用。

## 不打包直接用（更快）
直接双击项目根目录的 `start_mac.command`。
