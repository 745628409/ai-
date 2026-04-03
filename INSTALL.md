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

- Python 3.8+
- `requirements.txt`
- 打包工具：`pyinstaller`

## D. 签名与公证（正式分发建议）

如果你要给其他 Mac 用户“即装即用、无安全警告”体验，建议对 `.app` 和 `.dmg` 做 Apple Developer ID 签名与 notarization。
