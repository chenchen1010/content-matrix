---
name: first-run
description: 新用户首次使用引导，介绍框架能力并根据用户意图路由到对应 skill
---

# 首次使用引导

## 何时触发

当检测到以下任一条件时，自动运行此 skill：

1. 项目目录下不存在 `~/.content-matrix/config.json`
2. 用户说「我是新来的」「怎么开始」「这是什么」「帮我看看怎么用」
3. 会话中首次交互且用户意图不明确

## Step 1: 介绍

用以下话术向用户介绍（保持口语化，不要念文档）：

```
这是一个 AI 内容工厂。

你告诉我你是做什么行业的，我先去小红书、抖音上帮你摸底：
哪些内容火、同行怎么做的、你的潜在客户在搜什么、他们在什么决策阶段。

摸完底，再结合你自己的业务素材（客户案例、服务故事等），
批量生成适配各平台的内容，直接发布。

核心流程：
  搜 → 你这个行业什么内容火，同行怎么做的，用户在搜什么
  存 → 把调研结果和你的业务素材存进知识库
  写 → 基于调研 + 素材，批量生成多平台内容
  发 → 一键发布到小红书、抖音、公众号、视频号

你可以跑全流程，也可以只用其中一步。
```

## Step 2: 问用户想做什么

```
你现在想做什么？

1. 搜选题 — 看看你这个行业什么内容火，找灵感和方向
2. 录素材 — 把你的客户案例、业务故事录入知识库
3. 写内容 — 给你一段素材，帮你生成小红书/抖音/公众号文案
4. 跑全流程 — 从搜选题到发布，一条龙
5. 随便看看 — 先了解一下有哪些能力
```

等待用户回答。不要替用户选择。

## Step 3: 按意图检测依赖 + 路由

根据用户选择，检测对应的最小依赖集，缺什么补什么，然后路由到对应 skill。

### 选 1 → 搜选题

**需要**：小红书 MCP 运行中

```bash
mcporter list 2>/dev/null | grep -i xiaohongshu
```

- 已启动 → 路由到 `topic-scout` skill
- 未启动 → 运行 `platform-login` skill 引导登录 + 启动 MCP，完成后路由到 `topic-scout`

### 选 2 → 录素材

**需要**：知识库后端已就绪（Obsidian 或飞书，二选一）

先问用户选择存储方式：

```
素材存在哪里？

A. 本地 Obsidian（推荐个人使用，数据在自己电脑上）
B. 飞书知识库（推荐团队协作，数据在云端）
```

#### 选 A → Obsidian

```bash
obsidian-cli print-default --path-only 2>/dev/null
```

- 有默认 vault → 路由到 `obsidian-kb` 流程 2（口述录入）
- 无默认 vault → 路由到 `obsidian-kb` 流程 1（初始化知识库），完成后进入口述录入
- obsidian-cli 未安装 → 执行 `brew install yakitrak/yakitrak/obsidian-cli`，装完继续

#### 选 B → 飞书知识库

```bash
command -v lark-cli &>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"
```

- lark-cli 未安装 → 引导安装：
  ```bash
  npm install -g @larksuite/cli
  npx skills add larksuite/cli -y -g
  ```
- lark-cli 已安装但未登录 → 引导登录：
  ```bash
  # 首次需要配置应用凭证
  lark-cli config init --new
  # 然后登录并授权
  lark-cli auth login --as user --scope "wiki:wiki wiki:wiki:readonly wiki:node wiki:node:readonly docx:document docx:document:readonly drive:drive drive:drive:readonly search:docs_data:read"
  ```
  告知用户：「会打开浏览器让你授权飞书，授权完就可以了。」
- lark-cli 已安装已登录 → 路由到 `feishu-drive` skill

### 选 3 → 写内容

**需要**：无额外依赖（素材可以直接粘贴）

直接路由到 `content-generator` skill。告知用户：

```
你可以直接粘贴素材文本给我，也可以告诉我从知识库里找。
需要我从知识库检索，还是你直接给我素材？
```

### 选 4 → 跑全流程

**需要**：小红书 MCP + 知识库后端（Obsidian 或飞书）

按顺序检测，缺一个补一个：

```bash
# 1. 知识库后端（任一即可）
HAS_OBSIDIAN=$(obsidian-cli print-default --path-only 2>/dev/null && echo "yes" || echo "no")
HAS_LARK=$(command -v lark-cli &>/dev/null && echo "yes" || echo "no")

# 2. 小红书 MCP
mcporter list 2>/dev/null | grep -i xiaohongshu || echo "NEED_XHS_MCP"
```

- 两个知识库后端都没有 → 按「选 2」流程引导用户选择并配置一个
- 小红书 MCP 未启动 → 按「选 1」流程引导登录 + 启动

全部就绪后，路由到 `master-workflow` skill。

### 选 5 → 随便看看

列出能力清单：

```
以下是我能帮你做的事：

搜索类：
  • 搜小红书爆款内容，分析选题方向（topic-scout）
  • 搜抖音视频，转录文字稿（tools/search/douyin）
  • 读公众号文章，转成 Markdown（tools/search/wechat）

素材管理：
  • 口述录入客户案例、服务故事
  • 支持本地 Obsidian 或飞书知识库，二选一
  • 从飞书导出已有文档到本地（tools/collect/feishu-doc）

内容生产：
  • 基于素材批量生成多平台文案（content-generator）
  • 矩阵变体：同一素材出 3-5 个不同角度版本
  • 自动合规检查（广告法禁用词等）

发布：
  • 小红书、抖音、视频号、公众号一键发布
  • 发布后自动回写知识库，记录使用次数

排版：
  • 克隆任意公众号文章的排版风格（wechat-layout-clone）

告诉我你想试哪个？
```

## 注意事项

- 检测依赖时如果需要安装，由助手直接执行命令，不要让用户复制粘贴
- 每次只解决一个阻塞项，解决后再检测下一个，不要一次性抛出所有缺失
- 如果用户的回答不在 1-5 中，根据语义判断最接近的选项路由
- 如果用户说的是具体需求（如"帮我写一条小红书"），直接路由到对应 skill，跳过介绍
