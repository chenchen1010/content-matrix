---
name: first-run
description: 新用户首次使用引导，介绍框架后直接跑一次「搜选题 + 生成内容」体验流程
---

# 首次使用引导

## 何时触发

当检测到以下任一条件时，自动运行此 skill：

1. 项目目录下不存在 `~/.content-matrix/config.json`
2. 用户说「我是新来的」「怎么开始」「这是什么」「帮我看看怎么用」
3. 会话中首次交互且用户意图不明确

## Step 1: 介绍 + 收集信息

用以下话术向用户介绍（保持口语化，不要念文档）：

```
这是一个 AI 内容工厂。

你告诉我你做什么的，再给我 3 个你业务相关的关键词，
我直接去小红书上帮你摸底：哪些内容火、同行怎么做的、你的潜在客户在搜什么。

然后基于搜到的爆款，直接帮你生成 3 篇小红书笔记，连调研报告一起发到你飞书上。
你拿到就能直接用。

先简单介绍下你的业务，再给我 3 个种子关键词？
比如做杭州夜校的，可以给"杭州夜校"、"成人兴趣班"、"下班后学什么"。
```

等待用户回答。需要获取两个信息：
1. **业务介绍**（一两句话：做什么的、在哪个城市、目标客户是谁）
2. **3 个种子关键词**（用户最了解自己客户会搜什么）

> 如果用户只给了行业和城市没给关键词，主动帮他拟 3 个并确认。
> 如果用户给了 1-2 个词，追问补齐到 3 个。

## Step 2: 检测依赖并准备环境

体验流程需要两个依赖：小红书搜索 + 飞书交付。按顺序检测。

### 2a. 小红书 MCP

```bash
mcporter list 2>/dev/null | grep -i xiaohongshu
```

- 已启动 → 继续
- 未启动 → 运行 `platform-login` skill 引导登录 + 启动 MCP
  告知用户：「先帮你连上小红书，稍等一下。」

### 2b. 飞书 lark-cli

```bash
command -v lark-cli &>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"
```

- 未安装 → 安装并登录：
  ```bash
  npm install -g @larksuite/cli
  npx skills add larksuite/cli -y -g
  lark-cli config init --new
  lark-cli auth login --as user --scope "wiki:wiki wiki:node docx:document drive:drive search:docs_data:read bitable:app bitable:app:readonly im:message:send_as_bot"
  ```
  告知用户：「帮你装一个飞书工具，会弹浏览器让你授权一下。」
- 已安装未登录 → 只执行登录步骤
- 已安装已登录 → 继续

## Step 3: 搜选题（小红书）

用用户给的 3 个种子关键词调用 `topic-scout` skill，精简模式：

```
运行 topic-scout skill，精简模式：
- 平台：小红书
- 初始关键词：用户提供的 3 个种子关键词（全部搜，不是只搜 1 个）
- 只跑 1 轮搜索（3 个词各搜一次，不做后续迭代扩展）
- 每个关键词收集 5-8 条爆款笔记（共 15-24 条）
- 对每条笔记标注 A层
- 输出：选题报告 + 关键词库 + 客户画像
```

> 3 个关键词全部搜完，这样第一次结果就覆盖了不同维度，用户拿到的报告有足够信息做决策。

搜索完成后，告知用户进度：
```
3 个关键词都搜完了，共找到 {N} 条爆款内容。正在分析选题方向和用户画像...
```

## Step 4: 生成 3 篇小红书笔记

从 3 个关键词的搜索结果中，选 3 条最具代表性的爆款（尽量覆盖不同关键词 × 不同 A层），调用 `content-generator` skill：

```
运行 content-generator skill：
- 素材来源：Step 3 搜到的爆款中选 3 条（优先从不同关键词、不同 A层 各取一条）
- 模式：二创（基于爆款参考改写，融入用户的业务信息）
- 平台：小红书
- 数量：3 篇（分别对应不同选题角度）
- 目标 A层：各取一个（如 A2 研究型 + A3 对比型 + A4 避坑型）
- 融入信息：用户 Step 1 提供的业务介绍（城市、行业、目标客户等）
```

> 关键：3 篇笔记要覆盖不同方向，让用户看到这个工具的广度，而不是 3 篇同质内容。

## Step 5: 交付到飞书

### 5a. 创建飞书知识库存放调研报告

```bash
# 创建知识库
lark-cli api POST /open-apis/wiki/v2/spaces \
  --body '{"name": "{行业}内容调研", "description": "AI 内容工厂 — {行业}选题调研"}'
# 记录 space_id

# 写入选题报告
lark-cli docs +create \
  --title "选题报告 — {城市}{行业}" \
  --wiki-space "{space_id}" \
  --markdown "{Step 3 生成的选题报告内容}"

# 写入客户画像
lark-cli docs +create \
  --title "客户画像 — {行业}" \
  --wiki-space "{space_id}" \
  --markdown "{Step 3 生成的客户画像内容}"

# 写入关键词库
lark-cli docs +create \
  --title "长尾关键词库 — {行业}" \
  --wiki-space "{space_id}" \
  --markdown "{Step 3 生成的关键词库内容}"
```

### 5b. 创建飞书多维表格存放生成的笔记

```bash
# 创建多维表格
lark-cli api POST /open-apis/bitable/v1/apps \
  --body '{"name": "{行业} — 小红书笔记", "folder_token": ""}'
# 记录 app_token

# 创建数据表
lark-cli api POST /open-apis/bitable/v1/apps/{app_token}/tables \
  --body '{
    "table": {
      "name": "小红书笔记",
      "default_view_name": "全部笔记",
      "fields": [
        {"field_name": "标题", "type": 1},
        {"field_name": "正文", "type": 1},
        {"field_name": "标签", "type": 1},
        {"field_name": "A层", "type": 3, "property": {"options": [{"name":"A1"},{"name":"A2"},{"name":"A3"},{"name":"A4"},{"name":"A5"}]}},
        {"field_name": "选题角度", "type": 1},
        {"field_name": "参考爆款", "type": 15},
        {"field_name": "合规状态", "type": 3, "property": {"options": [{"name":"通过"},{"name":"需修改"}]}},
        {"field_name": "状态", "type": 3, "property": {"options": [{"name":"待审核"},{"name":"待发布"},{"name":"已发布"}]}}
      ]
    }
  }'
# 记录 table_id

# 写入 3 篇笔记
for each note in [笔记1, 笔记2, 笔记3]:
  lark-cli api POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records \
    --body '{
      "fields": {
        "标题": "{笔记标题}",
        "正文": "{笔记正文}",
        "标签": "{标签列表}",
        "A层": "{A层}",
        "选题角度": "{角度说明}",
        "参考爆款": "{原始爆款链接}",
        "合规状态": "{合规检查结果}",
        "状态": "待审核"
      }
    }'
```

### 5c. 发送飞书消息卡片给用户

```bash
# 获取用户自己的 user_id
USER_INFO=$(lark-cli api GET /open-apis/authen/v1/user_info)
USER_ID=$(echo "$USER_INFO" | jq -r '.data.user_id')

# 发送消息卡片
lark-cli api POST /open-apis/im/v1/messages \
  --params '{"receive_id_type": "user_id"}' \
  --body '{
    "receive_id": "'$USER_ID'",
    "msg_type": "interactive",
    "content": "{\"config\":{\"wide_screen_mode\":true},\"header\":{\"title\":{\"tag\":\"plain_text\",\"content\":\"AI 内容工厂 — {行业}首次调研完成\"},\"template\":\"blue\"},\"elements\":[{\"tag\":\"div\",\"text\":{\"tag\":\"lark_md\",\"content\":\"已完成 {行业} 小红书选题调研，生成 3 篇待审笔记。\"}},{\"tag\":\"hr\"},{\"tag\":\"div\",\"text\":{\"tag\":\"lark_md\",\"content\":\"**调研报告**\\n选题报告 / 客户画像 / 关键词库\"}},{\"tag\":\"action\",\"actions\":[{\"tag\":\"button\",\"text\":{\"tag\":\"plain_text\",\"content\":\"查看调研知识库\"},\"url\":\"{知识库链接}\",\"type\":\"primary\"}]},{\"tag\":\"hr\"},{\"tag\":\"div\",\"text\":{\"tag\":\"lark_md\",\"content\":\"**生成笔记（3 篇）**\\n{笔记1标题} · {笔记2标题} · {笔记3标题}\"}},{\"tag\":\"action\",\"actions\":[{\"tag\":\"button\",\"text\":{\"tag\":\"plain_text\",\"content\":\"查看多维表格\"},\"url\":\"{多维表格链接}\",\"type\":\"primary\"}]},{\"tag\":\"hr\"},{\"tag\":\"div\",\"text\":{\"tag\":\"lark_md\",\"content\":\"觉得不错？可以继续：\\n• 补充你的业务素材，生成更贴合你的内容\\n• 扩展到抖音、公众号、视频号\\n• 一键发布到各平台\"}}]}"
  }'
```

## Step 6: 收尾

告知用户：

```
搞定了！已经发到你飞书上了，你会收到一张消息卡片：

📊 调研知识库 — 包含选题报告、客户画像、关键词库
📝 多维表格 — 3 篇小红书笔记，可以直接审核编辑

这只是用平台爆款做的二创。如果你有自己的业务素材（客户案例、服务故事等），
补充进来后生成的内容会更贴合你的业务。

接下来你可以：
1. 录入你的业务素材 — 告诉我你的客户案例或服务故事
2. 继续深挖选题 — 跑完整 4 轮调研，覆盖更多关键词
3. 扩展到其他平台 — 抖音、公众号、视频号
4. 直接发布 — 把笔记发到小红书上

想做哪个？
```

## 注意事项

- 全程由助手执行所有命令，不让用户复制粘贴
- 依赖检测失败时只提示当前阻塞项，不一次性列出所有缺失
- topic-scout 精简模式只跑 1 轮，控制在 3-5 分钟内完成体验
- 如果用户一上来就说了具体需求（如"帮我写一条小红书"），跳过体验流程，直接路由到对应 skill
- 消息卡片中的链接从 lark-cli 返回的 token 拼接：`https://xxx.feishu.cn/wiki/{space_id}` 和 `https://xxx.feishu.cn/base/{app_token}`
