---
name: content-matrix
description: 第一版主编排：收集业务信息和 3 个关键词，完成小红书深度调研、生成 3 条示范笔记，并交付到飞书云文档。当用户说“帮我做选题调研”“看看小红书上这个行业怎么做”“给我一版选题报告”时触发。
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
  - 业务信息
  - 3 个种子关键词
  - 可选：城市 / 目标客户 / 业务身份
outputs:
  - 飞书云文档（内含调研报告、嵌入式选题库、3 条示范笔记）
---

# 第一版主工作流

第一版只聚焦一件事：
把“小红书选题调研”做成一个可以直接交付给用户的结果。

不是全平台内容工厂，
不是自动发布闭环，
不是一次性定终局，
而是先交付一版能直接拿去发、拿反馈、再继续迭代的选题作战稿。

## ⚠️ 子 Skill 加载规则（必须遵守）

本 skill 是编排层，不包含子 skill 的实现细节。执行任何子 skill 前，先读取对应的 SKILL.md。

### 子 Skill 路径清单

| 子 Skill 名称 | SKILL.md / README.md 路径 |
|---|---|
| `topic-scout` | `content-matrix/skills/topic-scout/SKILL.md` |
| `content-generator` | `content-matrix/skills/content-generator/SKILL.md` |
| `platform-login` | `content-matrix/skills/platform-login/SKILL.md` |
| `feishu-drive` | `content-matrix/skills/feishu-drive/SKILL.md` |
| `knowledge-base` | `content-matrix/skills/knowledge-base/SKILL.md` |
| `first-run` | `content-matrix/skills/first-run/SKILL.md` |

### 平台工具路径清单

| 工具类别 | 工具名称 | 文档路径 |
|---|---|---|
| 搜索 | 小红书搜索 | `content-matrix/skills/tools/search/xiaohongshu/README.md` |
| 交付 | 飞书文档 / 多维表格 | `content-matrix/skills/feishu-drive/SKILL.md` |

## 何时使用

当用户说以下意图时，使用此 skill：
- “帮我做选题调研”
- “看看小红书上这个行业怎么做”
- “给我一版选题报告”
- “帮我研究同行和用户需求”
- “我给你业务和关键词，你帮我出选题”

## 第一版默认模式

默认直接跑：

1. 收集业务信息和 3 个种子关键词
2. 运行小红书深度调研
3. 生成 3 条示范笔记
4. 交付到飞书云文档

不要默认切到：
- 多平台扩展
- 自动发布
- 回写学习
- 深层素材库管理

这些都属于后续迭代，不是第一版主目标。

## 工作流

### Step 1: 对齐业务背景

先确认：
- 用户做什么业务
- 在哪个城市 / 区域
- 目标客户是谁
- 在市场中的身份是什么（官方 / 商业机构 / 个人 / 聚合平台 / 内容号）
- 用户提供的 3 个种子关键词

如果缺少关键词或业务身份，优先补齐后再进入调研。

## Step 2: 运行 topic-scout 深度调研

调用 `topic-scout` skill，平台固定为小红书。

核心目标不是“列爆款”，而是输出：
- 行业现状
- 用户需求与搜索意图
- 玩家格局
- 有效打法
- 选题方向

必须特别分析以下对象：
- 广告笔记
- 蓝 V 官方号 / 品牌号
- 素人种草号
- KOC / 合作号
- 持续重复发同类结构的矩阵号

判断标准：
- 点赞
- 评论
- 活跃度
- 是否持续重复使用
- 是否形成多账号协同

只要有效，哪怕内容同质化，也可视为可参考打法。

### Step 3: 生成 3 条示范性小红书笔记

调用 `content-generator` skill：
- 平台固定：小红书
- 数量固定：3 条
- 基于 Step 2 的调研结果和代表性爆款参考
- 必须覆盖不同选题方向或不同用户阶段
- 用于“先发出去验证”，不是为了形成最终完稿库

生成完成后，除正文外，还应输出一个 demo notes JSON，结构为：

```json
{
  "demo_notes": [
    {
      "title": "标题",
      "stage": "A2",
      "angle": "研究 / 建立信任",
      "body": "正文",
      "tags": ["#标签1", "#标签2"]
    }
  ]
}
```

这个 JSON 将与 topic-scout 的 research payload 合并，再交给飞书交付脚本。

### Step 4: 飞书交付

第一版只交付到飞书生态。

最终交付是一份飞书云文档，文档里要包含：
- 业务背景
- 行业现状
- 玩家格局
- 有效打法分析
- 用户需求 / 搜索意图
- 选题建议
- 3 条示范笔记

同时创建一张选题库多维表格，并嵌入云文档中。

**落地实现（推荐）**：
使用脚本 `content-matrix/scripts/deliver_xiaohongshu_report.py` 完成飞书交付。

```bash
python3 content-matrix/scripts/deliver_xiaohongshu_report.py content-matrix/scripts/sample_xiaohongshu_report_payload.json --notify
```

脚本输入为一个 JSON payload，至少包含：
- 业务信息
- 关键词
- 调研结论（10 个 report sections）
- 10-15 条以上的选题库 rows
- 3 条示范笔记

如 research 和 notes 是分开的 JSON，可先用：

```bash
python3 content-matrix/scripts/compose_xiaohongshu_payload.py \
  --base content-matrix/scripts/sample_xiaohongshu_report_payload.json \
  --research /path/to/research.json \
  --notes /path/to/demo_notes.json \
  --output /path/to/final_payload.json
```

脚本输出：
- 创建飞书多维表格“选题库”
- 写入选题记录
- 创建飞书云文档
- 在文档中写入调研报告和 3 条示范笔记
- 在文档中附上多维表格链接（飞书通常会自动预览）
- 可选：发一条飞书消息通知自己

### Step 5: 告诉用户如何使用第一版结果

交付后要明确告诉用户：
- 这不是一锤定音的最终策略
- 重点是先把方向跑出来
- 先拿 3 条示范内容和优先选题去发
- 根据真实反馈再继续迭代

## 对用户的输出口径

尽量用这样的表达：

```
我已经把这版小红书调研整理成飞书文档了。

里面不是单纯的爆款汇总，而是：
- 这个行业在小红书上的现状
- 同行和不同玩家正在用哪些有效打法
- 用户分别在关注什么、担心什么
- 哪些选题值得优先做
- 以及 3 条可以直接开始测试的小红书笔记

你先拿这版去发，拿到反馈后，我们再继续迭代下一版。
```

## 第一版成功标准

只要达成以下几点，就算成功：
- 用户清楚知道“小红书上现在什么打法有效”
- 用户拿到一份可执行选题库
- 用户拿到 3 条可以马上开始发的示范笔记
- 交付集中在飞书文档里，便于阅读和继续协作

## 暂不纳入第一版的内容

以下内容默认不做，除非用户明确要求：
- 自动发布到平台
- 多平台扩展（抖音 / 视频号 / 公众号）
- Obsidian 知识库沉淀
- 发布后自动回写
- 深度素材库建设
- 复杂运营自动化
