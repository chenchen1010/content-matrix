---
name: feishu-drive
description: 基于飞书云空间的业务素材知识库，对标 obsidian-kb 提供相同工作流
---

# 飞书云空间知识库

基于飞书云空间（Drive + DocX），管理业务素材知识库。
对标 `obsidian-kb` skill，提供相同的 5 个工作流程，底层读写使用飞书 Open API。

## 核心原则：一个项目 = 一个文件夹

每个业务/行业/客户项目对应飞书云空间中一个独立的项目文件夹。不同项目的素材不混在一起。

> 文件夹结构与 Obsidian vault 一致，见 `content-matrix/schemas/vault-structure.md`。

## 何时使用

- "帮我记一下这个客户案例"、"录入素材" → 口述录入
- "看看知识库里有什么"、"找关于XX的素材" → 检索素材
- "帮我搭建知识库"、"初始化素材库" → 知识库初始化（创建新项目）
- "切换到XX项目" → 切换当前项目
- "整理一下知识库" → 知识库维护

## 前置条件

1. 配置文件已创建：`~/.content-organizer/config.json`
2. 飞书自建应用已开通 Drive 和 DocX 相关权限

## 工作流程

### 流程 1: 创建新项目知识库

```bash
cd content-matrix/skills/feishu-drive
python3 feishu_drive.py init {项目名}
```

会在飞书云空间中创建完整的文件夹结构：
```
{项目名}/
└── 素材库/
    ├── 1-客户案例/
    ├── 2-交付故事/
    ├── 3-行业知识/
    ├── 4-爆款参考/小红书/ & 抖音/
    ├── 5-选题报告/
    ├── 6-内容产出/小红书/ & 抖音/ & 公众号/ & 视频号/
    ├── 10-发布日志/
    ├── 8-长尾关键词库/
    └── 9-客户画像/
```

项目信息自动写入 `~/.content-organizer/config.json`。

### 流程 2: 口述录入

**Step 1:** 用户口述业务故事

**Step 2:** AI 自动结构化为 Markdown（含 YAML frontmatter），按 obsidian-kb 相同的模板格式

**Step 3:** 写入飞书
```bash
# 方式一：从文件写入
python3 feishu_drive.py write {项目名} "1-客户案例/张姐-深度保洁" /tmp/note.md

# 方式二：从 stdin 写入
echo "..." | python3 feishu_drive.py write {项目名} "1-客户案例/张姐-深度保洁" -
```

**Step 4:** 向用户展示飞书链接，确认内容。

### 流程 3: 检索素材

**方式一：按目录浏览**
```bash
python3 feishu_drive.py list {项目名}
python3 feishu_drive.py list {项目名} "1-客户案例"
```

**方式二：关键词搜索**
```bash
python3 feishu_drive.py search {项目名} "保洁"
```

**方式三：读取具体文档**
```bash
python3 feishu_drive.py read {项目名} {文档token}
```

AI 对搜索结果进行相关性排序，优先推荐 frontmatter 中 `used_count` 较低的素材。

### 流程 4: 发布后回写

内容发布后，更新素材文档的 frontmatter：

```bash
# 读取原文 → 修改 frontmatter → 写回
python3 feishu_drive.py read {项目名} {文档token} > /tmp/note.md
# AI 修改 used_count、status 等字段
python3 feishu_drive.py update {项目名} {文档token} /tmp/note.md
```

同时在 `10-发布日志/` 下创建发布记录文档。

### 流程 5: 知识库健康检查

```bash
python3 feishu_drive.py list {项目名}
python3 feishu_drive.py list {项目名} "1-客户案例"
python3 feishu_drive.py list {项目名} "4-爆款参考/小红书"
# ... 逐目录统计
```

AI 分析各目录文档数量并生成健康报告。

## 数据格式兼容

与 Obsidian 使用相同的笔记格式（YAML frontmatter + Markdown 正文）。frontmatter 在飞书文档中存为顶部的 YAML 代码块，读回时自动解析。

笔记模板、标签体系、双链策略均与 `obsidian-kb/SKILL.md` 保持一致。

## 快捷用法

- "我有个故事想记下来" → 流程 2 口述录入
- "帮我搭建知识库" → 流程 1 初始化
- "找保洁相关的素材" → 流程 3 检索
- "知识库情况怎么样" → 流程 5 健康检查
