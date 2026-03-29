---
name: feishu-drive
description: 基于飞书知识库的业务素材管理，使用 lark-cli 操作知识库和文档
inputs:
  - 操作类型（初始化 / 录入 / 检索 / 回写 / 健康检查）
  - 项目名 / 关键词 / 素材内容
outputs:
  - 飞书知识库中的文档（结构与 Obsidian vault 一致，见 schemas/vault-structure.md）
---

# 飞书知识库

基于飞书知识库（Wiki）+ DocX 文档，管理业务素材。
对标 `obsidian-kb` skill，提供相同的工作流程，底层使用 `lark-cli` 操作。

> 文件夹结构与 Obsidian vault 一致，见 `content-matrix/schemas/vault-structure.md`。

## 核心原则：一个项目 = 一个知识库

每个业务/行业/客户项目对应飞书中一个独立的知识库（Wiki Space）。不同项目的素材不混在一起。

## 何时使用

- "帮我记一下这个客户案例"、"录入素材" → 口述录入
- "看看知识库里有什么"、"找关于XX的素材" → 检索素材
- "帮我搭建知识库"、"初始化素材库" → 知识库初始化
- "切换到XX项目" → 切换当前项目
- "整理一下知识库" → 知识库维护

## 前置条件

### 安装 lark-cli

```bash
npm install -g @larksuite/cli
npx skills add larksuite/cli -y -g
```

### 登录飞书

```bash
# 首次配置应用凭证（会打开浏览器授权）
lark-cli config init --new

# 登录并获取知识库相关权限
lark-cli auth login --as user --scope "wiki:wiki wiki:wiki:readonly wiki:node wiki:node:readonly docx:document docx:document:readonly drive:drive drive:drive:readonly search:docs_data:read"
```

### 验证

```bash
lark-cli docs +search --query "test" --count 1
```

能返回结果即表示登录成功。

---

## 工作流程

### 流程 1: 创建新项目知识库

**Step 1:** 创建知识库空间

```bash
lark-cli api POST /open-apis/wiki/v2/spaces --body '{"name": "{项目名}", "description": "内容矩阵 — {项目名}素材库"}'
```

记录返回的 `space_id`。

**Step 2:** 在知识库中创建目录结构

飞书知识库的"目录"就是节点（node）。按 `schemas/vault-structure.md` 定义的结构，逐层创建：

```bash
SPACE_ID="{上一步的 space_id}"

# 创建根节点「素材库」
lark-cli api POST /open-apis/wiki/v2/spaces/$SPACE_ID/nodes \
  --body '{"obj_type": "docx", "title": "素材库"}'
# 记录返回的 node_token 作为 MATERIAL_ROOT_NODE

# 在素材库下创建各子节点
for NAME in "1-客户案例" "2-交付故事" "3-行业知识" "5-选题报告" "7-选题库" "8-长尾关键词库" "9-客户画像" "10-发布日志"; do
  lark-cli api POST /open-apis/wiki/v2/spaces/$SPACE_ID/nodes \
    --body "{\"obj_type\": \"docx\", \"title\": \"$NAME\", \"parent_node_token\": \"$MATERIAL_ROOT_NODE\"}"
done

# 4-爆款参考（含子节点）
lark-cli api POST /open-apis/wiki/v2/spaces/$SPACE_ID/nodes \
  --body '{"obj_type": "docx", "title": "4-爆款参考", "parent_node_token": "'$MATERIAL_ROOT_NODE'"}'
# 记录 node_token 作为 REF_NODE，然后创建子节点
lark-cli api POST /open-apis/wiki/v2/spaces/$SPACE_ID/nodes \
  --body '{"obj_type": "docx", "title": "小红书", "parent_node_token": "'$REF_NODE'"}'
lark-cli api POST /open-apis/wiki/v2/spaces/$SPACE_ID/nodes \
  --body '{"obj_type": "docx", "title": "抖音", "parent_node_token": "'$REF_NODE'"}'

# 6-内容产出（含子节点）
lark-cli api POST /open-apis/wiki/v2/spaces/$SPACE_ID/nodes \
  --body '{"obj_type": "docx", "title": "6-内容产出", "parent_node_token": "'$MATERIAL_ROOT_NODE'"}'
# 记录 node_token 作为 OUTPUT_NODE
for PLATFORM in "小红书" "抖音" "公众号" "视频号"; do
  lark-cli api POST /open-apis/wiki/v2/spaces/$SPACE_ID/nodes \
    --body "{\"obj_type\": \"docx\", \"title\": \"$PLATFORM\", \"parent_node_token\": \"$OUTPUT_NODE\"}"
done
```

**Step 3:** 保存项目配置

将 `space_id` 和关键 `node_token` 写入 `~/.content-matrix/config.json`：

```json
{
  "feishu": {
    "projects": {
      "{项目名}": {
        "space_id": "xxx",
        "material_root_node": "xxx",
        "nodes": {
          "1-客户案例": "node_token_xxx",
          "2-交付故事": "node_token_xxx",
          ...
        }
      }
    },
    "current_project": "{项目名}"
  }
}
```

### 流程 2: 口述录入

**Step 1:** 用户口述业务故事

**Step 2:** AI 自动结构化为 Markdown（含 YAML frontmatter），按 obsidian-kb 相同的模板格式

**Step 3:** 写入飞书知识库

```bash
# 从配置中读取目标节点
PROJECT="{项目名}"
# 在「1-客户案例」节点下创建文档
lark-cli docs +create \
  --title "{客户称呼}-{服务类型}-{亮点}" \
  --wiki-node "{1-客户案例的 node_token}" \
  --markdown "{结构化的 Markdown 内容}"
```

**Step 4:** 向用户展示飞书链接，确认内容。

### 流程 3: 检索素材

**方式一：全局搜索**

```bash
lark-cli docs +search --query "{关键词}" --count 20
```

**方式二：读取具体文档**

先解析 wiki token 得到真实 doc token：

```bash
# 如果有 wiki URL，先解析
lark-cli wiki spaces get_node --params '{"token": "{wiki_token}"}'
# 拿到 obj_token 后读取
lark-cli docs +fetch --document-id "{obj_token}"
```

**方式三：列出节点下的文档**

```bash
lark-cli api GET /open-apis/wiki/v2/spaces/{space_id}/nodes \
  --params '{"parent_node_token": "{node_token}", "page_size": 50}'
```

AI 对搜索结果进行相关性排序，优先推荐 frontmatter 中 `used_count` 较低的素材。

### 流程 4: 发布后回写

内容发布后，更新素材文档的 frontmatter：

```bash
# 读取原文
lark-cli docs +fetch --document-id "{doc_token}" > /tmp/note.md
# AI 修改 used_count、status 等字段后写回
lark-cli docs +update --document-id "{doc_token}" --mode overwrite --markdown "{修改后的内容}"
```

同时在「10-发布日志」节点下创建发布记录：

```bash
lark-cli docs +create \
  --title "{日期}-发布记录" \
  --wiki-node "{10-发布日志的 node_token}" \
  --markdown "{发布记录内容}"
```

### 流程 5: 知识库健康检查

```bash
SPACE_ID="{space_id}"
# 逐节点统计文档数
for NODE_NAME in "1-客户案例" "2-交付故事" "3-行业知识" "4-爆款参考" "5-选题报告" "6-内容产出"; do
  NODE_TOKEN="{从 config.json 读取}"
  lark-cli api GET /open-apis/wiki/v2/spaces/$SPACE_ID/nodes \
    --params '{"parent_node_token": "'$NODE_TOKEN'"}'
done
```

AI 分析各目录文档数量并生成健康报告。

## 数据格式兼容

与 Obsidian 使用相同的笔记格式（YAML frontmatter + Markdown 正文）。lark-cli 的 `docs +create` 接受标准 Markdown，读回时通过 `docs +fetch` 获取。

笔记模板、标签体系均与 `obsidian-kb/SKILL.md` 保持一致。

## 快捷用法

- "我有个故事想记下来" → 流程 2 口述录入
- "帮我搭建知识库" → 流程 1 初始化
- "找保洁相关的素材" → 流程 3 检索
- "知识库情况怎么样" → 流程 5 健康检查
