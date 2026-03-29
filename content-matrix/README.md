# AI 内容矩阵操盘工具包

一套自包含的 AI 内容营销工具包：从选题、素材管理、内容生成到发布，全流程闭环。

## 一键安装

```bash
cd content-matrix
./setup.sh
```

## 架构原则：框架与数据分离

```
content-matrix/                              ← 框架层（GitHub 同步，不含用户数据）
├── setup.sh                                 ← 一键安装
├── .env.example                             ← 配置模板
├── schemas/
│   └── vault-structure.md                   ← Vault 目录结构唯一定义
├── config/
│   └── config.example.json
├── scripts/
│   └── check-update.sh                      ← 框架版本检查
└── skills/                                  ← 所有 skill + tool 代码
    ├── master-workflow/SKILL.md              ← 总编排
    ├── topic-scout/SKILL.md                 ← 选题侦察
    ├── content-generator/                   ← 内容生成
    │   ├── SKILL.md
    │   └── templates/                       ← 平台 prompt 模板
    ├── knowledge-base/                      ← 知识底座
    ├── obsidian-kb/SKILL.md                 ← 知识库管理
    ├── material-library/SKILL.md            ← 素材路由
    ├── wechat-layout-clone/SKILL.md         ← 公众号排版复刻
    ├── platform-login/SKILL.md              ← 平台登录引导
    ├── framework-sync/SKILL.md              ← 框架版本同步
    ├── framework-contribute/SKILL.md        ← 经验回馈
    └── tools/                               ← 平台工具
        ├── search/                          ← 搜索类
        │   ├── xiaohongshu/                 ← 小红书搜索/详情
        │   ├── douyin/                      ← 抖音视频解析
        │   └── wechat/                      ← 公众号文章搜索+阅读
        ├── publish/                         ← 发布类
        │   ├── xiaohongshu/                 ← 小红书发布（MCP）
        │   ├── douyin/                      ← 抖音发布（Stagehand）
        │   ├── wechat-channels/             ← 视频号发布（短视频）
        │   └── wechat-article/              ← 公众号发布（文章）
        └── collect/                         ← 采集类
            └── feishu-doc/                  ← 飞书文档导出

~/Desktop/黑曜石/{项目名}/                     ← 用户数据层（Obsidian vault，不在 git 中）
└── 素材库/                                   ← 所有业务产出（结构见 schemas/vault-structure.md）

~/.content-matrix/                            ← 运行时配置（不在 git 中）
├── .env                                      ← API 密钥
├── cookies/                                  ← 平台登录凭证
├── cache/                                    ← 缓存文件
└── downloads/                                ← 采集工具临时输出
```

**关键规则**：框架目录（`content-matrix/`）内只有代码和模板，零用户数据。所有产出写入 Obsidian vault 或 `~/.content-matrix/`。

## 全流程

```
选题侦察 → 素材检索 → 内容生成 → 内容发布 → 数据回写
(topic-scout) (material-library) (content-generator) (tools/publish) (obsidian-kb)
     ↓              ↓                  ↓                ↓              ↓
 tools/search    obsidian-kb       平台模板          tools/publish   Obsidian vault
```

由 `master-workflow` 统一编排，一条命令跑完全流程。

## Skills

| Skill | 功能 |
|-------|------|
| **topic-scout** | 搜索平台爆款，分析选题方向，存入知识库 |
| **content-generator** | 基于素材+选题生成多平台内容，支持矩阵变体 |
| **obsidian-kb** | 业务知识库管理（一项目一 vault） |
| **wechat-layout-clone** | 从任意公众号图文抽取内联样式，归纳成可复用主题 |
| **material-library** | 素材库路由（Obsidian / 飞书） |
| **master-workflow** | 总编排：选题→素材→生成→发布→回写 |
| **platform-login** | 引导抖音/小红书登录：由 AI 代跑脚本，不要求用户复制终端命令 |

## Tools

### 搜索类 (skills/tools/search/)

| 工具 | 平台 | 能力 | 来源 |
|------|------|------|------|
| **xiaohongshu-mcp** | 小红书 | 搜索/详情/发布 | [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) |
| **douyin_mcp** | 抖音 | 关键词搜索/视频详情 | [hhy5562877/douyin_mcp](https://github.com/hhy5562877/douyin_mcp) |
| **douyin-mcp-server** | 抖音 | 视频解析/ASR（火山引擎或阿里云） | [yzfly/douyin-mcp-server](https://github.com/yzfly/douyin-mcp-server) |
| **yt-dlp** | 抖音 | 视频元数据/字幕下载 | [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| **miku_ai** | 微信公众号 | 文章搜索 | [PyPI](https://pypi.org/project/miku-ai/) |
| **wechat-article-for-ai** | 微信公众号 | 文章阅读（Camoufox） | 内置 |

### 发布类 (skills/tools/publish/)

| 工具 | 平台 | 方式 | 来源 |
|------|------|------|------|
| **xiaohongshu-mcp** | 小红书 | MCP `publish_content` | 同搜索 |
| **publish-dy.mjs** | 抖音 | Stagehand + Playwright | 内置 |
| **wechat-channels/** | 视频号 | Stagehand + Playwright | 内置 |
| **wechat-article/** | 公众号 | API + 文言排版 + Evolink 封面 | 内置 |

## 前置依赖（不打包，需自行安装）

- **Node.js** >= 18
- **Python** >= 3.10
- **obsidian-cli**：`brew install yakitrak/brew/obsidian`
- **mcporter**：`npm install -g mcporter`
- **Jina Reader**：云服务，无需安装

## 快速开始

```bash
# 1. 安装
./setup.sh

# 2. 配置
cp .env.example .env
# 编辑 .env 填入 API Key

# 3. 登录（首次或 Cookie 过期）— 推荐方式，无需手抄命令
#    • 对 AI 说：「帮我登录抖音 / 小红书」→ 会运行 platform-login 流程
#    • 或 Cmd+Shift+P → 「Tasks: Run Task」→「内容矩阵 · 抖音登录」或「小红书登录」

# 4. 启动小红书 MCP（同样可请 AI 执行，或运行任务「启动小红书 MCP」）

# 5. 初始化知识库
# 在 AI 中说："帮我搭建一个「夜校」的知识库"

# 6. 开始使用
# "帮我做一套小红书内容"         → 全流程
# "帮我搜小红书上教育培训的爆款"  → 只选题
# "用知识库素材写一条抖音"        → 只生成
# "把昨天的内容发布了"            → 只发布
```
