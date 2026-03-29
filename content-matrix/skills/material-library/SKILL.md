---
name: material-library
description: 素材管理入口层，根据配置自动选择 Obsidian 或飞书作为素材存储后端
inputs:
  - 操作类型（录入 / 检索 / 管理）
  - 关键词或素材内容
outputs:
  - 路由到 obsidian-kb 或 feishu-drive，产出写入用户数据层
---

# 素材库路由

素材管理的入口层，根据用户配置自动选择素材存储方案。

> **架构原则**：本 skill 是纯路由层，不直接写入任何文件。所有存储操作委托给 obsidian-kb 或 feishu-drive。

## 路由逻辑

```
检查 obsidian-cli 是否可用：
  obsidian-cli print-default --path-only 2>/dev/null

├─ 可用 → 使用 obsidian-kb skill（Obsidian 知识库）
└─ 不可用 → 检查飞书
    ├─ lark-cli 可用（command -v lark-cli）→ 使用 feishu-drive skill（飞书知识库）
    └─ 都没有 → 提示用户选择并配置
```

## 何时使用

当用户说"帮我管理素材"、"录入素材"、"找素材"时，先运行路由逻辑判断使用哪个后端。

## Obsidian 路径（推荐）

检测到 obsidian-cli 可用时，转交 `obsidian-kb` skill 处理。

详见 `obsidian-kb/SKILL.md`。

## 飞书路径

检测到 `lark-cli` 可用时，转交 `feishu-drive` skill 处理。

飞书路径使用知识库（Wiki Space）+ DocX 文档，通过 `lark-cli` 操作，结构与 Obsidian vault 一致。

### 核心命令

```bash
# 搜索素材
lark-cli docs +search --query "{关键词}" --count 20

# 创建文档
lark-cli docs +create --title "{标题}" --wiki-node "{node_token}" --markdown "{内容}"

# 读取文档
lark-cli docs +fetch --document-id "{doc_token}"

# 更新文档
lark-cli docs +update --document-id "{doc_token}" --mode overwrite --markdown "{内容}"
```

详见 `feishu-drive/SKILL.md`。

## 快捷用法

- "录入一个客户案例" → 路由判断后执行对应 skill
- "从飞书拉素材" → 直接走飞书路径
- "从知识库找素材" → 直接走 Obsidian 路径
