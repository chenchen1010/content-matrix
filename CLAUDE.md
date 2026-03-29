# Project Rules

## gstack

所有网页浏览操作必须使用 gstack 的 `/browse` skill，禁止使用 `mcp__claude-in-chrome__*` 工具。

可用的 gstack skills：
- `/office-hours` — 办公时间
- `/plan-ceo-review` — CEO 评审计划
- `/plan-eng-review` — 工程评审计划
- `/plan-design-review` — 设计评审计划
- `/design-consultation` — 设计咨询
- `/review` — 代码评审
- `/ship` — 发布
- `/browse` — 网页浏览（所有浏览操作必须使用此 skill）
- `/qa` — 质量保证
- `/qa-only` — 仅 QA
- `/design-review` — 设计评审
- `/setup-browser-cookies` — 设置浏览器 cookies
- `/retro` — 回顾
- `/debug` — 调试
- `/document-release` — 发布文档

## content-matrix（本仓库）

### 核心架构原则：框架与数据分离

- **框架层**（`content-matrix/`）：只有 skills 代码、模板、脚本。通过 GitHub 同步。
- **用户数据层**（Obsidian vault / 飞书）：所有业务产出。不在 git 中。
- **运行时配置**（`~/.content-matrix/`）：API 密钥、cookies、缓存。不在 git 中。
- **唯一目录结构定义**：`content-matrix/schemas/vault-structure.md`，所有 skill 引用它而非各自定义。
- **禁止在 `content-matrix/skills/` 下写入任何用户数据文件**（downloads、images、progress.json 等）。

### 会话启动：首次使用检测

每次新会话，在更新检查之后，检测用户是否首次使用：

```bash
test -f ~/.content-matrix/config.json && echo "RETURNING_USER" || echo "NEW_USER"
```

- 输出 `NEW_USER` → 读取 `content-matrix/skills/first-run/SKILL.md` 并执行引导流程
- 输出 `RETURNING_USER` → 跳过，直接进入用户的工作

### 平台登录

用户要登录抖音搜索（douyin_search）或小红书 MCP 时：**不要**让用户复制终端命令。应读取并遵循 `content-matrix/skills/platform-login/SKILL.md`，由助手代执行脚本，或提示 **Cmd+Shift+P → Tasks: Run Task →「内容矩阵 · 抖音/小红书登录」**。

### 会话启动：自动检查框架更新

每次新会话开始时，在响应用户的第一个请求之前，先运行更新检查：

```bash
bash content-matrix/scripts/check-update.sh 2>/dev/null || true
```

- 输出 `UP_TO_DATE` → 不提示，直接进入用户的工作
- 输出 `UPGRADE_AVAILABLE ...` → 读取 `content-matrix/skills/framework-sync/SKILL.md` 并按其中的「更新提醒流程」引导用户
- 检查失败或超时 → 静默跳过，不打断用户

### 经验回馈：识别框架级改动

当用户在会话中修改了 SKILL.md、templates/、scripts/ 或 CLAUDE.md 等框架文件时，在合适的时机（如任务告一段落时）主动询问是否回馈。具体流程见 `content-matrix/skills/framework-contribute/SKILL.md`。

**不要对 .env、cookies.json、Obsidian vault 内容等个人文件触发回馈提醒。**
