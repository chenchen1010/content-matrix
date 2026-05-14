# 小红书选题调研助手

第一版聚焦一件事：
用户提供业务信息 + 3 个种子关键词，助手直接跑一版小红书深度调研，输出飞书云文档报告，并附带嵌入式选题库和 3 条示范笔记。

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

## 第一版交付流程

```
业务信息 + 3 个关键词
        ↓
小红书深度调研
        ↓
行业现状 + 用户需求 + 有效打法分析
        ↓
选题库 + 3 条示范笔记
        ↓
飞书云文档交付（内嵌多维表格）
```

由 `master-workflow` 统一编排，默认走“小红书深度选题调研 + 3 条示范笔记 + 飞书交付”。

## Skills

| Skill | 功能 |
|-------|------|
| **first-run** | 新用户首次引导：收集业务信息和 3 个关键词，直接跑深度版 |
| **master-workflow** | 总编排：小红书深度调研 → 选题 → 3 条示范笔记 → 飞书交付 |
| **topic-scout** | 搜索平台爆款，分析行业现状、玩家打法、用户需求和选题方向 |
| **content-generator** | 基于调研结果生成 3 条示范性小红书笔记 |
| **obsidian-kb** | 业务知识库管理（一项目一 vault） |
| **material-library** | 素材库路由（Obsidian / 飞书） |
| **wechat-layout-clone** | 从任意公众号图文抽取内联样式，归纳成可复用主题 |
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

### 交付类

第一版默认只交付到飞书，不包含自动发布闭环。

| 工具 | 用途 |
|------|------|
| **lark-cli** | 创建飞书云文档 / 多维表格 / 消息通知 |
| **xiaohongshu-mcp** | 提供小红书搜索、详情和评论抓取能力 |

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

# 5. 开始使用
# 对 AI 说：
# "我做杭州成人夜校，目标客户是 22-35 岁上班族。
#  关键词是：杭州夜校、成人兴趣班、下班后学什么。"
```

## 第一版用户会拿到什么

一份飞书云文档，里面包含：

- 行业现状
- 用户需求与搜索意图
- 同行/官方号/广告/KOC/素人号的有效打法分析
- 一份可执行的选题库（嵌入多维表格）
- 3 条示范性小红书笔记

这不是“一锤定音”的最终策略，而是一份能直接拿去发布、收集反馈、继续迭代的第一版作战稿。
