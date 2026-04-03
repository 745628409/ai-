# 视频镜头智能检索（macOS 10.14 兼容增强版）

这是一个可在 **macOS 10.14 (Mojave)** 上运行的本地应用：

- 导入视频
- 自动切分镜头（shot detection）
- 生成每个镜头缩略图 + 时间点
- 自然语言检索（动作、景别、光影、空镜、反应镜头等）
- 演员面部检索（通过演员图库）
- 特效场面检索（自动特效标签 + 查询加权）
- 事件级近似检索（走进门、睁眼、行走）
- 场景约束检索（`scene:` 前缀）

## 1. 环境要求

- macOS 10.14
- Python 3.8~3.11（推荐 3.10）
- 已安装 `ffmpeg`

## 2. 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. 运行

```bash
python app/main.py
```

## 4. 使用说明

### 4.1 建立镜头索引

1) 点击“导入视频并建立索引”
2) 程序会自动进行镜头切分，并为每个镜头抽取多帧关键帧
3) 程序会自动生成特效标签与场景标签

### 4.2 演员面部检索

在项目目录中准备演员图库：

```text
data/
  actors/
    Tom/
      1.jpg
      2.jpg
    Alice/
      1.jpg
```

然后点击“加载演员库(data/actors)”。

### 4.3 查询语法（支持组合）

- 演员：`actor:Tom`
- 场景：`scene:门口`
- 事件词：`走进门` / `睁开眼` / `行走`

示例：

```text
actor:Tom scene:门口 走进门
actor:Alice scene:走廊 睁开眼
scene:办公室 行走
```

> 组合查询会触发融合排序：语义相似度 + 特效标签 + 场景标签 + 事件加权 + 演员匹配。

## 5. 检索准确率增强策略（本版已实现）

- 多关键帧索引：每段镜头抽样多帧，而非仅中点帧
- 融合排序：全局语义分 + 特效/场景标签加权 + 事件加权 + 演员人脸相似度加权
- 事件启发式：针对“走进门 / 睁眼 / 行走”加入专门加权（含睁眼检测启发）
- 命中解释：结果显示“命中依据”以便人工快速判断

## 6. 后续可扩展方向

- 台词级检索：Whisper 转写 + 时间轴对齐
- 演员识别增强：接入专业人脸识别模型（ArcFace/InsightFace）
- 景别/角度/机位专用分类器：微调电影镜头数据集
- 剪辑流程对接：导出 EDL / CSV / Premiere 标记


## 7. 如何下载安装（你关心的即装即用）

目前仓库里提供了 **macOS 一键打包脚本**，可以在 Mac 上直接生成 `.dmg`：

```bash
bash scripts/build_macos_dmg.sh
```

生成物：

- `dist/ShotSearch.app`
- `ShotSearch.dmg`

安装时双击 `ShotSearch.dmg`，把 `ShotSearch.app` 拖进 `Applications` 即可。

详细步骤见：`INSTALL.md`。


## 8. Windows 10 版本（可打包）

已提供 Windows 打包脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows_exe.ps1
```

生成：

- `dist\ShotSearch\ShotSearch.exe`

将 `dist\ShotSearch` 整个目录打包给用户即可使用。


> 如果 macOS 打包时出现 `opencv` 安装失败，`build_macos_dmg.sh` 会自动尝试 `requirements-macos-legacy.txt`，并自动轮询多个 `opencv-python` 二进制 wheel 版本（含 Mojave 可用的历史版本），避免触发本地 CMake/nasm 源码编译。
