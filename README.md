# Novel2Screen MVP（小说文本生成画面与视频）

> 给编程小白：**最简单只要 1 条命令**，就能自动打开网页使用。

## 一、最简单使用方式（推荐）

### Windows
1. 双击 `start.bat`
2. 等待安装完成
3. 浏览器会自动打开：`http://127.0.0.1:8000`

### macOS / Linux
```bash
./start.sh
```
然后浏览器打开：`http://127.0.0.1:8000`

### 通用（任何系统）
```bash
pip install -r backend/requirements.txt
python run.py
```

> 页面是中文，打开后直接粘贴小说段落，按按钮就能生成图片和视频。

---

## 二、你能做什么

- 文本生成静态画面（多候选、风格、比例）
- 文本生成视频（自动拆镜头）
- 图像生成视频（动作描述）
- 关键帧补全视频（开头/中间/结尾）
- 小说理解（人物、场景、情绪、动作、镜头建议）
- 角色卡与历史记录

---

## 三、环境变量（可选）

复制：
```bash
cp .env.example .env
```

- 默认 `MOCK_MODE=true`：不用填 API Key 也可演示全流程。
- 若要真实生成：填入 `OPENAI_API_KEY` 和 `REPLICATE_API_TOKEN`。

---

## 四、API 调用示例

见：`docs/api-examples.md`

---

## 五、项目结构

```text
ai-/
├─ run.py                      # 一键启动（自动开浏览器）
├─ start.sh                    # macOS/Linux 一键启动
├─ start.bat                   # Windows 一键启动
├─ backend/
│  ├─ app/
│  │  ├─ main.py               # API + 首页
│  │  ├─ static_index.html     # 小白可直接用的中文网页
│  │  ├─ config.py
│  │  ├─ models/schemas.py
│  │  └─ services/
│  │     ├─ story_parser.py
│  │     ├─ model_service.py
│  │     └─ storage_service.py
│  └─ requirements.txt
├─ frontend/                   # React 前端（进阶开发可用）
├─ docs/api-examples.md
└─ .env.example
```
