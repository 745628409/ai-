# API 调用示例

## 1) 小说理解
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"text":"夜晚的走廊里，一个女人缓慢走向尽头的门，灯光闪烁，她回头看了一眼"}'
```

## 2) 文本生成静态画面
```bash
curl -X POST http://localhost:8000/api/generate/image \
  -H 'Content-Type: application/json' \
  -d '{
    "text":"夜晚的走廊里，一个女人缓慢走向尽头的门，灯光闪烁，她回头看了一眼",
    "style":"悬疑",
    "aspect_ratio":"16:9",
    "candidate_count":3,
    "character_ids":[]
  }'
```

## 3) 文本生成视频
```bash
curl -X POST http://localhost:8000/api/generate/video/text \
  -H 'Content-Type: application/json' \
  -d '{
    "text":"夜晚的走廊里，一个女人缓慢走向尽头的门，灯光闪烁，她回头看了一眼",
    "style":"电影感",
    "aspect_ratio":"16:9",
    "duration_seconds":6,
    "character_ids":[]
  }'
```

## 4) 图像生成视频
```bash
curl -X POST http://localhost:8000/api/generate/video/image \
  -H 'Content-Type: application/json' \
  -d '{
    "image_url":"https://picsum.photos/seed/story/1366/768",
    "action_text":"角色慢慢抬头，风吹动头发，镜头向前推进",
    "style":"电影感",
    "duration_seconds":6
  }'
```

## 5) 关键帧补全视频
```bash
curl -X POST http://localhost:8000/api/generate/video/keyframes \
  -H 'Content-Type: application/json' \
  -d '{
    "start_image_url":"https://picsum.photos/seed/start/1366/768",
    "middle_image_url":"https://picsum.photos/seed/mid/1366/768",
    "end_image_url":"https://picsum.photos/seed/end/1366/768",
    "story_text":"人物从走廊入口走向尽头，最后停在门前",
    "style":"电影感",
    "duration_seconds":8
  }'
```
