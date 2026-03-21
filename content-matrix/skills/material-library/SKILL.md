---
name: material-library
description: 素材管理入口层，根据配置自动选择 Obsidian 或飞书作为素材存储后端
---

# 素材库路由

素材管理的入口层，根据用户配置自动选择素材存储方案。

## 路由逻辑

```
检查 obsidian-cli 是否可用：
  obsidian-cli print-default --path-only 2>/dev/null

├─ 可用 → 使用 obsidian-kb skill（Obsidian 知识库）
└─ 不可用 → 检查飞书配置
    ├─ ~/.content-organizer/config.json 存在 → 使用 feishu-drive skill（飞书云空间）
    └─ 都没有 → 提示用户选择并配置
```

## 何时使用

当用户说"帮我管理素材"、"录入素材"、"找素材"时，先运行路由逻辑判断使用哪个后端。

## Obsidian 路径（推荐）

检测到 obsidian-cli 可用时，转交 `obsidian-kb` skill 处理。

详见 `obsidian-kb/SKILL.md`。

## 飞书路径

检测到 `~/.content-organizer/config.json` 时，转交 `feishu-drive` skill 处理。

飞书路径使用云空间（Drive）的文件夹 + DocX 文档，文件夹结构与 Obsidian vault 完全一致。

### 核心脚本

```bash
SCRIPT_DIR="content-matrix/skills/feishu-drive"

# 初始化项目
python3 "$SCRIPT_DIR/feishu_drive.py" init {项目名}

# 写入素材
python3 "$SCRIPT_DIR/feishu_drive.py" write {项目名} "{路径}" {md文件}

# 列出目录
python3 "$SCRIPT_DIR/feishu_drive.py" list {项目名} [路径]

# 搜索素材
python3 "$SCRIPT_DIR/feishu_drive.py" search {项目名} {关键词}

# 读取文档
python3 "$SCRIPT_DIR/feishu_drive.py" read {项目名} {文档token}

# 更新文档
python3 "$SCRIPT_DIR/feishu_drive.py" update {项目名} {文档token} {md文件}
```

详见 `feishu-drive/SKILL.md`。

## 快捷用法

- "录入一个客户案例" → 路由判断后执行对应 skill
- "从飞书拉素材" → 直接走飞书路径
- "从知识库找素材" → 直接走 Obsidian 路径
