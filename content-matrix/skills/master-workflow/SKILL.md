---
name: content-matrix
description: 内容矩阵主编排：选题→素材→生成→发布→回写，一键跑通全流程。当用户说"帮我做一套内容"、"跑一遍全流程"、"一键产出"、"内容矩阵"时触发。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - WebSearch
  - WebFetch
inputs:
  - 用户指令（"帮我做一套内容" / "跑一遍全流程" 等）
  - 可选：指定选题、指定素材、指定平台
outputs:
  - 由子 skill 写入 Obsidian vault（见 schemas/vault-structure.md）
---

# 内容矩阵主工作流

一键跑通从选题到发布的完整闭环。

> **架构原则**：框架归框架，产出归产出。本 skill 只做编排调度，所有数据产出由子 skill 写入用户的 Obsidian vault（或飞书），框架目录内不存任何用户数据。
> 目录结构见 `content-matrix/schemas/vault-structure.md`。

## 何时使用

当用户说"帮我做一套内容"、"跑一遍全流程"、"一键产出"时使用此 skill。

## 工作模式

### 模式 1: 全自动（默认）

完整运行：选题 → 素材 → 生成 → 发布 → 回写

### 模式 2: 指定选题

跳过选题步骤，用户提供选题方向，运行：素材 → 生成 → 发布 → 回写

### 模式 3: 指定素材

跳过选题和素材步骤，用户提供素材，运行：生成 → 发布 → 回写

### 模式 4: 只生成不发布

任何模式都可以加"先不发"，跳过发布步骤，只到内容生成为止。

## 全自动工作流程

### Step 1: 选题侦察

调用 `topic-scout` skill（使用 `skills/tools/search/` 下的平台工具）：

```
请运行 topic-scout skill，帮我在{平台}上搜索与"{用户的行业}"相关的爆款内容。
```

topic-scout 会：
1. 搜索平台爆款
2. 把每条搜索结果存入 Obsidian `项目/{项目名}/爆款参考/{平台}/`
3. 生成选题报告存入 `项目/{项目名}/选题报告/`
4. 输出推荐选题

让用户从推荐选题中选择 1-3 个方向。

### Step 2: 素材检索

调用 `material-library` skill（自动路由到 Obsidian 或飞书）：

```
请运行 material-library skill，搜索与选题"{选定的选题}"相关的素材。
```

如果知识库中没有匹配素材，提示用户：
```
知识库中没有找到与此选题直接相关的素材。你可以：
1. 口述一个相关的客户案例/故事（我来结构化录入）
2. 粘贴一段相关素材文本
3. 用选题报告中的爆款参考作为灵感来源
4. 换一个有素材支撑的选题
```

### Step 3: 内容生成

调用 `content-generator` skill：

```
请运行 content-generator skill：
- 素材：{Step 2 获取的素材}
- 选题：{Step 1 选定的选题}
- 平台：{用户指定或默认全平台}
- 数量：{用户指定或默认每平台 3 个版本}
```

content-generator 会自动将产出内容存入 Obsidian `项目/{项目名}/内容产出/{平台}/`。

### Step 4: 内容发布

**发布前必须让用户确认。** 展示所有生成的内容摘要，等用户确认后执行发布。

```
=== 待发布内容 ===

小红书（3 条）：
  1. {标题} — {变体说明}
  2. {标题} — {变体说明}
  3. {标题} — {变体说明}

抖音（1 条）：
  1. {标题}

视频号（1 条）：
  1. {标题}

公众号（1 条）：
  1. {标题}

确认发布到以上平台？（全部发布 / 选择性发布 / 暂不发布）
```

用户确认后，按平台调用 `skills/tools/publish/` 下的工具：

#### 小红书发布

```bash
mcporter call 'xiaohongshu.publish_content(title: "{标题}", content: "{正文}", images: ["{图片路径}"], tags: ["{标签}"])'
```

> 详见 `skills/tools/publish/xiaohongshu/README.md`

#### 抖音发布

```bash
node skills/tools/publish/douyin/publish-dy.mjs \
  --video="{视频路径}" \
  --desc="{描述}" \
  --title="{标题}"
```

> 详见 `skills/tools/publish/douyin/README.md`

#### 视频号发布

```bash
node skills/tools/publish/wechat-channels/publish-sph.mjs \
  --video="{视频路径}" \
  --desc="{描述}" \
  --original
```

> 详见 `skills/tools/publish/wechat-channels/README.md`

#### 公众号发布（文章）

```bash
python3 skills/tools/publish/wechat-article/publish.py \
  --app-id "$WECHAT_APP_ID" --app-secret "$WECHAT_APP_SECRET" \
  --markdown "{Markdown文件路径}" \
  --title "{标题}"
```

#### 公众号发布（小绿书）

将一组信息图/图片发布为公众号"小绿书"格式（图片消息），最多 20 张。
当用户说"发小绿书"、"发图片消息"、"发信息图"时使用此模式。

```bash
python3 skills/tools/publish/wechat-article/publish.py \
  --app-id "$WECHAT_APP_ID" --app-secret "$WECHAT_APP_SECRET" \
  --title "{标题}" \
  --image-dir "{图片目录}" \
  --type 小绿书
```

> 详见 `skills/tools/publish/wechat-article/README.md`

### Step 5: 数据回写

发布完成后，调用 `obsidian-kb` 更新记录：

1. 更新 `项目/{项目名}/内容产出/` 中对应笔记的 frontmatter：
   - `status: 已发布`
   - `published_at: {时间}`
   - `published_platforms: [{平台列表}]`

2. 更新引用素材的 `used_count` + 1

3. 在 `项目/{项目名}/发布日志/` 中记录本次发布：
   ```
   项目/{项目名}/发布日志/{年-月}/{日期}-发布记录.md
   ```

### Step 6: 输出汇总

```
=== 内容矩阵产出报告 ===

📅 日期: {今天日期}
🎯 选题: {选题方向}
📦 素材来源: {使用的素材笔记名}

--- 小红书 ---
版本 1: {标题} ✅ 已发布
版本 2: {标题} ✅ 已发布
版本 3: {标题} ✅ 已发布

--- 抖音 ---
版本 1: {标题} ✅ 已发布

--- 视频号 ---
版本 1: {标题} ✅ 已发布

--- 公众号（文章） ---
版本 1: {标题} ✅ 已发布

--- 公众号（小绿书） ---
版本 1: {标题} ✅ 已发布（{N}张图片）

=== 共产出 {N} 条内容，已发布 {M} 条 ===

✅ 所有数据已回写 Obsidian 知识库
```

## 快捷用法

- "帮我做一套小红书内容" → 全自动模式，平台锁定小红书
- "帮我做一套内容，先不发" → 模式 4，跳过发布
- "用这个素材帮我做矩阵" → 模式 3，跳过选题和素材检索
- "今天的选题是XX，帮我产出" → 模式 2，跳过选题步骤
- "把昨天生成的内容发布了" → 直接跳到 Step 4，从 Obsidian 读取待发布内容
- "把这组图片发小绿书" → 直接调用公众号小绿书发布（`--type 小绿书`）
- "采集这篇文章的图片发到公众号" → 用 browse 采集图片 → 小绿书发布
