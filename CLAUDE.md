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

用户要登录抖音搜索（douyin_search）或小红书 MCP 时：**不要**让用户复制终端命令。应读取并遵循 `content-matrix/skills/platform-login/SKILL.md`，由助手代执行脚本，或提示 **Cmd+Shift+P → Tasks: Run Task →「内容矩阵 · 抖音/小红书登录」**。
