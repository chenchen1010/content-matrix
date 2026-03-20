# 知识库镜像（仓库内）

与 `obsidian-kb` 中 **「一个项目 = 一个 vault」** 的目录约定对齐，便于：

- 在**未安装 obsidian-cli** 或 **vault 在另一台机器** 时，仍在 git 仓库里留存结构化素材；
- 需要时用 `cp -R` 或 Obsidian「打开文件夹为库」同步到 `~/Desktop/黑曜石/夜校`。

## 当前结构

```
knowledge-mirror/夜校/素材库/
├── 4-爆款参考/抖音/     ← 抖音爆款拆解、批次占位、转录
└── 5-选题报告/          ← 各渠道选题报告（含抖音）
```

可按 `obsidian-kb/SKILL.md` 继续补全 `1-客户案例` … `7-发布日志` 等目录。

## 与抖音 MCP 的关系

真实 **搜索 + 口播转录** 依赖本机：

- `douyin_search` + `douyin` MCP
- 有效 `cookies.txt`
- `content-matrix/.env` 中 ASR 密钥

详见 `content-matrix/skills/tools/search/douyin/README.md`。
