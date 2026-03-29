---
name: obsidian-kb
description: 基于 Obsidian 的业务素材知识库管理，支持素材入库、检索和知识图谱
---

# Obsidian 业务知识库

基于 OpenClaw 的 `@steipete/obsidian` skill，管理业务素材知识库。
本 skill 提供**业务层面**的知识库编排设计，底层读写依赖 `obsidian-cli`。

## 核心原则：一个项目 = 一个 vault

每个业务/行业/客户项目对应一个独立的 Obsidian vault。不同项目的素材不混在一起。

示例：
- `~/Desktop/黑曜石/夜校/` — 夜校项目的所有素材、选题、产出
- `~/Desktop/黑曜石/家政/` — 家政项目的所有素材、选题、产出

用 `obsidian-cli set-default` 切换当前工作项目。

## 何时使用

- "帮我记一下这个客户案例"、"录入素材" → 口述录入
- "看看知识库里有什么"、"找关于XX的素材" → 检索素材
- "帮我搭建知识库"、"初始化素材库" → 知识库初始化（创建新项目 vault）
- "切换到XX项目" → 切换默认 vault
- "整理一下知识库" → 知识库维护

## 前置条件

### 1. 安装 obsidian-cli

```bash
brew tap yakitrak/yakitrak
brew install yakitrak/yakitrak/obsidian-cli
```

### 2. 安装 OpenClaw Obsidian skill

```bash
openclaw add @steipete/obsidian
```

### 3. 设置当前项目 vault

```bash
# 查看已有 vault
obsidian-cli print-default

# 切换到某个项目
obsidian-cli set-default "夜校"
```

### 4. 验证

```bash
obsidian-cli print-default --path-only && echo "✅ OK"
```

---

## 知识库编排设计

### Vault 结构

> **权威定义见 `content-matrix/schemas/vault-structure.md`**，本 skill 不重复定义完整结构。
> 以下仅列出本 skill 直接操作的目录。

本 skill 直接操作的目录：
- `素材库/1-客户案例/` — 口述录入的客户故事
- `素材库/2-交付故事/` — 口述录入的服务花絮
- `素材库/3-行业知识/` — 专业知识录入
- `素材库/10-发布日志/{YYYY-MM}/` — 发布后回写记录
- `素材库/_模板/` — 笔记模板文件

### 双链关系

全流程的产出通过 `[[双链]]` 串联：
```
爆款参考/素材 ←→ 选题报告（素材支撑了哪个选题）
选题报告 ←→ 内容产出（选题产出了哪些内容）
内容产出 ←→ 素材来源（这条内容用了哪个素材）
发布日志 ←→ 内容产出（发了哪些内容、数据表现）
```

### 笔记模板

#### 客户案例模板
```markdown
---
type: 客户案例
industry: {{行业}}
region: {{地区}}
date: {{日期}}
tags:
  - 客户案例
  - {{行业标签}}
  - {{地区标签}}
used_count: 0
platforms_used: []
status: 未使用
---

# {{客户称呼}} — {{一句话概括}}

## 背景
- 客户是谁：
- 遇到的问题：
- 怎么找到我们的：

## 服务过程
- 做了什么：
- 花了多长时间：
- 过程中的亮点/意外：

## 结果
- 客户反馈（最好是原话）：
- 前后对比：
- 数据（如有）：

## 可提炼的内容角度
1. 
2. 
3. 

## 关键金句
> "（客户的原话，或者印象深刻的细节）"
```

#### 交付故事模板
```markdown
---
type: 交付故事
industry: {{行业}}
region: {{地区}}
date: {{日期}}
tags:
  - 交付故事
  - {{行业标签}}
emotion: {{温暖/搞笑/感动/励志}}
used_count: 0
status: 未使用
---

# {{故事标题}}

## 发生了什么
（用第一人称，像跟朋友聊天一样讲）

## 为什么值得记录
（这个故事有什么特别的？能让读者产生什么感受？）

## 可提炼的内容角度
1. 
2. 

## 关键细节
- 时间：
- 地点：
- 人物：
- 转折点：
```

#### 爆款拆解模板
```markdown
---
type: 爆款参考
platform: {{平台}}
original_url: {{原始链接}}
date_collected: {{采集日期}}
likes: {{点赞数}}
tags:
  - 爆款参考
  - {{平台}}
  - {{行业标签}}
---

# {{爆款标题}}

## 数据表现
- 平台：
- 点赞/收藏/评论：

## 内容拆解
- 标题公式：
- 开头 Hook：
- 内容结构：
- CTA 方式：

## 为什么火
（核心原因：选题好？情绪共鸣？实用价值？）

## 我能怎么用
（如何将这个思路用到自己的业务内容中）
```

### 标签体系

```
├── 素材类型：#客户案例 #交付故事 #行业知识 #爆款参考
├── 行业：#家政 #教育 #电商 #餐饮 ...
├── 地区：#上海 #北京 #海外华人 ...
├── 平台：#小红书 #抖音 #视频号 #公众号
├── 情绪：#温暖 #搞笑 #感动 #励志 #干货
├── 使用状态：#未使用 #已使用 #高频复用
└── 内容角度：#避坑 #对比 #教程 #故事 #清单
```

### 双链策略

在笔记正文中用 `[[笔记名]]` 创建关联：
- 客户案例 ←→ 交付故事（同一客户的多次服务）
- 客户案例 ←→ 行业知识（案例验证了哪条行业认知）
- 爆款参考 ←→ 客户案例（这个爆款思路可以用哪个客户故事来做）
- 内容日志 ←→ 素材来源（这条内容用了哪些素材）

---

## 工作流程

### 流程 1: 创建新项目知识库

**Step 1:** 向用户确认项目名称（如"夜校"、"家政"）。

**Step 2:** 创建 vault 目录和素材库结构：

```bash
PROJECT_NAME="夜校"  # 用户指定的项目名
VAULT_PATH=~/Desktop/黑曜石/$PROJECT_NAME
MATERIAL_ROOT="$VAULT_PATH/素材库"

# 创建 vault（含 .obsidian 最小配置）
mkdir -p "$VAULT_PATH/.obsidian"
echo '{}' > "$VAULT_PATH/.obsidian/app.json"
echo '{}' > "$VAULT_PATH/.obsidian/appearance.json"

# 创建素材库目录结构
mkdir -p "$MATERIAL_ROOT/1-客户案例"
mkdir -p "$MATERIAL_ROOT/2-交付故事"
mkdir -p "$MATERIAL_ROOT/3-行业知识"
mkdir -p "$MATERIAL_ROOT/4-爆款参考/小红书"
mkdir -p "$MATERIAL_ROOT/4-爆款参考/抖音"
mkdir -p "$MATERIAL_ROOT/5-选题报告"
mkdir -p "$MATERIAL_ROOT/6-内容产出/小红书"
mkdir -p "$MATERIAL_ROOT/6-内容产出/抖音"
mkdir -p "$MATERIAL_ROOT/6-内容产出/公众号"
mkdir -p "$MATERIAL_ROOT/6-内容产出/视频号"
mkdir -p "$MATERIAL_ROOT/7-选题库"
mkdir -p "$MATERIAL_ROOT/8-长尾关键词库"
mkdir -p "$MATERIAL_ROOT/9-客户画像"
mkdir -p "$MATERIAL_ROOT/10-发布日志/$(date +%Y-%m)"
mkdir -p "$MATERIAL_ROOT/_模板"
```

**Step 3:** 将模板文件写入 `_模板/` 目录。

**Step 4:** 提示用户在 Obsidian 中打开这个 vault：
```bash
# 在 Obsidian 中打开新 vault
open "obsidian://open?vault=$PROJECT_NAME"
```

如果 Obsidian 提示 vault 不存在，需要用户在 Obsidian 中手动 Open folder as vault。

**Step 5:** 将新 vault 设为 obsidian-cli 默认：
```bash
obsidian-cli set-default "$PROJECT_NAME"
```

### 流程 1b: 切换项目

```bash
# 切换到另一个项目
obsidian-cli set-default "家政"

# 验证
obsidian-cli print-default --path-only

# 在 Obsidian 中打开
open "obsidian://open?vault=家政"
```

### 流程 2: 口述录入

**Step 1:** 用户口述业务故事

**Step 2:** AI 自动结构化
```
请将以下口述内容结构化为客户案例笔记：

口述内容：{用户的口述}

要求：
1. 填充客户案例模板的所有字段（含 frontmatter）
2. 自动推断行业、地区、标签
3. 提炼 3 个可做内容的角度
4. 提取关键金句
5. 生成文件名（格式：客户称呼-服务类型-亮点.md）
6. 识别是否可以 [[双链]] 到已有笔记
```

**Step 3:** 通过 obsidian-cli 创建笔记
```bash
VAULT_PATH=$(obsidian-cli print-default --path-only)
NOTE_PATH="素材库/1-客户案例/家政/张姐-深度保洁-朋友圈推荐.md"

cat > "$VAULT_PATH/$NOTE_PATH" << 'NOTEEOF'
{结构化的笔记内容，含 frontmatter}
NOTEEOF

# 在 Obsidian 中打开（可选）
obsidian-cli open "$NOTE_PATH"
```

**Step 4:** 向用户确认并询问是否需要补充。

### 流程 3: 检索素材

搜索采用 2 级降级策略：先尝试 obsidian-cli（需 Obsidian 打开对应 vault），失败则用 grep 兜底。

**Level 1: obsidian-cli 搜索（需 Obsidian 运行且已打开目标 vault）**

```bash
# 按内容搜索
obsidian-cli search-content "保洁 客户" 2>/dev/null

# 按笔记名搜索
obsidian-cli search "张姐" 2>/dev/null
```

如果返回 `Cannot find note in vault` 或为空，说明 Obsidian 未打开此 vault，自动降级到 Level 2。

**Level 2: grep 直接搜索（始终可用）**

```bash
VAULT_PATH=$(obsidian-cli print-default --path-only)
MATERIAL_ROOT="$VAULT_PATH/素材库"

# 按关键词搜索内容
grep -r -l "保洁" "$MATERIAL_ROOT/" --include="*.md"

# 搜索并显示匹配行（带上下文）
grep -r -n -C 2 "保洁" "$MATERIAL_ROOT/" --include="*.md"

# 按标签筛选
grep -r -l "客户案例" "$MATERIAL_ROOT/" --include="*.md"

# 查找未使用的素材
grep -r -l "used_count: 0" "$MATERIAL_ROOT/" --include="*.md"
```

**按目录浏览：**
```bash
VAULT_PATH=$(obsidian-cli print-default --path-only)
ls "$VAULT_PATH/素材库/1-客户案例/家政/"
```

读取搜索结果后，AI 进行相关性排序：
```
从以下搜索结果中，找出与选题"{选题方向}"最相关的素材。
按相关度排序，给出推荐理由。
优先推荐 frontmatter 中 used_count 较低的素材。
```

### 流程 4: 内容发布后回写

内容生成并发布后，更新素材的使用记录：

```bash
VAULT_PATH=$(obsidian-cli print-default --path-only)
NOTE_FILE="$VAULT_PATH/素材库/1-客户案例/家政/张姐-深度保洁-朋友圈推荐.md"

# AI 直接读取文件内容，修改 frontmatter 中的 used_count +1，然后写回
```

同时在内容日志中记录本次发布：
```bash
LOG_DIR="$VAULT_PATH/素材库/10-发布日志/$(date +%Y-%m)"
mkdir -p "$LOG_DIR"
cat > "$LOG_DIR/$(date +%m%d)-${PLATFORM}-${TOPIC}.md" << 'LOGEOF'
---
type: 发布日志
date: {日期}
platform: {平台}
topic: {选题}
source_materials:
  - "[[素材笔记名1]]"
  - "[[素材笔记名2]]"
---
# {日期} {平台} 发布记录

## 发布内容
{生成的内容摘要}

## 使用素材
{引用的素材列表，用 [[双链]]}
LOGEOF
```

### 流程 5: 知识库健康检查

```bash
VAULT_PATH=$(obsidian-cli print-default --path-only)
MATERIAL_ROOT="$VAULT_PATH/素材库"

echo "=== 素材统计 ==="
echo "客户案例: $(find "$MATERIAL_ROOT/1-客户案例" -name "*.md" | wc -l | tr -d ' ')"
echo "交付故事: $(find "$MATERIAL_ROOT/2-交付故事" -name "*.md" | wc -l | tr -d ' ')"
echo "行业知识: $(find "$MATERIAL_ROOT/3-行业知识" -name "*.md" | wc -l | tr -d ' ')"
echo "爆款参考: $(find "$MATERIAL_ROOT/4-爆款参考" -name "*.md" | wc -l | tr -d ' ')"
echo "发布日志: $(find "$MATERIAL_ROOT/10-发布日志" -name "*.md" | wc -l | tr -d ' ')"

echo ""
echo "=== 未使用素材 ==="
grep -r -l "used_count: 0" "$MATERIAL_ROOT/" --include="*.md" 2>/dev/null | head -10

echo ""
echo "=== 本月新增 ==="
find "$MATERIAL_ROOT" -name "*.md" -newer "$MATERIAL_ROOT" -mtime -30 | wc -l | tr -d ' '
```

AI 分析统计结果并生成健康报告和建议。

## 快捷用法

- "我有个故事想记下来" → 流程 2 口述录入
- "帮我搭建知识库" → 流程 1 初始化
- "找保洁相关的素材" → 流程 3 智能检索
- "知识库情况怎么样" → 流程 5 健康检查
