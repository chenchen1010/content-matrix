# 小红书发布队列

## 工作流

```
content-generator 生成内容
        ↓
  写入 JSON 到 pending/
        ↓
  RPA 扫描 pending/ 目录
        ↓
  移动到 publishing/（锁定，防重复消费）
        ↓
  解析 JSON → 逐字段填写小红书创作者页面
        ↓
   ┌─ 成功 → 回填 published_at → 移到 done/
   └─ 失败 → 回填 error → 移到 failed/
```

## 目录结构

```
output/xiaohongshu/
├── post-schema.json     ← JSON Schema，字段说明
├── pending/             ← 待发布
├── publishing/          ← 发布中（RPA 正在处理）
├── done/                ← 已发布
├── failed/              ← 发布失败
└── README.md            ← 本文件
```

## 文件命名

```
xhs-{YYYYMMDD}-{HHmmss}-{variant}.json
```

示例：`xhs-20260319-153000-v1.json`

## JSON 字段与小红书页面的映射

| JSON 字段 | 小红书页面操作 | 必填 | 默认值 |
|-----------|--------------|------|--------|
| `post_type` | 选择"图文"/"视频"/"长文"标签页 | 否 | `image_text` |
| `files` | 点击上传区域，选择图片/视频文件 | 是 | — |
| `cover_index` | 点击对应图片设为封面 | 否 | `0`（第一张） |
| `title` | 填写标题输入框 | 是 | — |
| `content` | 填写正文编辑区 | 是 | — |
| `tags` | 话题标签列表，每项含 # 号，如 ["#上海家政", "#保洁推荐"]（最多 10 个） | 否 | `[]` |
| `location` | 点击"添加地点"，搜索并选择 | 否 | `null` |
| `mentions` | @用户列表，每项含 @ 符号，如 ["@家政小王", "@上海生活指南"] | 否 | `[]` |
| `group_chat` | 点击"选择群聊"，搜索并勾选 | 否 | `null` |
| `schedule` | 点击"定时发布"，设置日期时间（格式 `YYYY-MM-DD HH:mm`） | 否 | `null`（立即发布） |
| `product` | 点击"添加商品"，填商品名或商品 ID（最多 1 个） | 否 | `""` |
| `file` | 点击"选择文件"，上传笔记附件 | 否 | `null` |

## RPA 处理逻辑（伪代码）

```python
import json, shutil, glob
from pathlib import Path

QUEUE = Path("output/xiaohongshu")

for f in sorted(glob.glob(str(QUEUE / "pending/*.json"))):
    src = Path(f)
    dst = QUEUE / "publishing" / src.name
    shutil.move(src, dst)

    post = json.loads(dst.read_text("utf-8"))

    try:
        # 1. 上传文件
        upload_files(post["files"])

        # 2. 设置封面
        if post.get("cover_index") is not None:
            set_cover(post["cover_index"])

        # 3. 填标题
        fill_title(post["title"])

        # 4. 填正文
        fill_content(post["content"])

        # 5. 添加标签
        for tag in post.get("tags", []):
            add_tag(tag)

        # 6. 添加地点
        if post.get("location"):
            add_location(post["location"])

        # 6.5 添加 @用户
        for mention in post.get("mentions", []):
            add_mention(mention)

        # 7. 选择群聊
        if post.get("group_chat"):
            select_group_chat(post["group_chat"])

        # 8. 定时发布
        if post.get("schedule"):
            set_schedule(post["schedule"])
        
        # 9. 添加商品（最多 1 个）
        if post.get("product"):
            add_product(post["product"])

        # 10. 选择文件（笔记附件）
        if post.get("file"):
            upload_attachment(post["file"])

        # 11. 点击发布
        click_publish()

        # 成功 → 回填并移到 done/
        post["meta"]["status"] = "done"
        post["meta"]["published_at"] = now_iso()
        dst.write_text(json.dumps(post, ensure_ascii=False, indent=2))
        shutil.move(dst, QUEUE / "done" / dst.name)

    except Exception as e:
        # 失败 → 回填并移到 failed/
        post["meta"]["status"] = "failed"
        post["meta"]["error"] = str(e)
        dst.write_text(json.dumps(post, ensure_ascii=False, indent=2))
        shutil.move(dst, QUEUE / "failed" / dst.name)
```

## RPA 集成

- `extract_json_data.py`：解析 JSON，返回 13 个变量的元组，供 RPA 解包
- `RPA_兼容性说明.md`：RPA 环境调试经验、常见错误与修复

## 扩展

- 同样的模式可复用到 `output/douyin/`、`output/wechat-channels/`、`output/wechat-article/` 等平台
- 每个平台有自己的 schema 和字段映射
- `meta.obsidian_note` 支持发布后自动回写 Obsidian 状态
