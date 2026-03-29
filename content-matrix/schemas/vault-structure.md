# Vault 目录结构定义（唯一权威）

所有 skill 在创建、读取、写入 vault 时必须遵循此结构。不要在各自 SKILL.md 中重复定义。

## 目录结构

```
{项目名} vault/
└── 素材库/
    ├── 1-客户案例/                  ← 真实客户故事（最高价值素材）
    ├── 2-交付故事/                  ← 服务过程中的细节和花絮
    ├── 3-行业知识/                  ← 专业知识、避坑指南、定价逻辑
    ├── 4-爆款参考/                  ← 从平台采集的优质内容拆解
    │   ├── 小红书/
    │   └── 抖音/
    ├── 5-选题报告/                  ← topic-scout 的搜索分析结果
    ├── 6-内容产出/                  ← content-generator 生成的内容
    │   ├── 小红书/
    │   ├── 抖音/
    │   ├── 公众号/
    │   └── 视频号/
    ├── 7-选题库/                    ← topic-scout 输出的选题推荐
    ├── 8-长尾关键词库/              ← topic-scout 输出的关键词库
    ├── 9-客户画像/                  ← topic-scout 输出的用户画像
    ├── 10-发布日志/                 ← 发布后的记录
    │   └── {YYYY-MM}/
    └── _模板/
        ├── 客户案例模板.md
        ├── 交付故事模板.md
        ├── 行业知识模板.md
        └── 爆款拆解模板.md
```

## 路径约定

| 变量名 | 含义 | 获取方式 |
|--------|------|---------|
| `VAULT_PATH` | 当前项目 vault 根目录 | `obsidian-cli print-default --path-only` |
| `MATERIAL_ROOT` | 素材库根目录 | `$VAULT_PATH/素材库` |

## 各 skill 写入位置

| Skill | 写入目录 | 文件名规则 |
|-------|---------|-----------|
| topic-scout | `4-爆款参考/{平台}/` | `{标题}.md` |
| topic-scout | `5-选题报告/` | `{日期}-{关键词}-{平台}选题报告.md` |
| topic-scout | `7-选题库/` | `{日期}-{业务}-选题库.md` |
| topic-scout | `8-长尾关键词库/` | `{日期}-{业务}-关键词库.md` |
| topic-scout | `9-客户画像/` | `{日期}-{业务}-客户画像.md` |
| content-generator | `6-内容产出/{平台}/` | `{日期}-{平台}-{变体标签}.md` |
| master-workflow | `10-发布日志/{YYYY-MM}/` | `{日期}-发布记录.md` |
| obsidian-kb | `1-客户案例/` | `{客户称呼}-{服务类型}-{亮点}.md` |
| obsidian-kb | `2-交付故事/` | `{故事标题}.md` |
| obsidian-kb | `3-行业知识/` | `{主题}.md` |

## Frontmatter 公共字段

所有素材笔记必须包含：

```yaml
type: {素材类型}        # 客户案例 | 交付故事 | 行业知识 | 爆款参考 | 内容产出 | 选题报告 | ...
date: {YYYY-MM-DD}
tags: []
used_count: 0           # 被 content-generator 引用的次数
status: 未使用           # 未使用 | 已使用 | 已发布
```

## 运行时文件位置

运行时产生的状态文件不在 vault 中，也不在框架目录中：

| 文件 | 位置 | 用途 |
|------|------|------|
| 平台 Cookie | `~/.content-matrix/cookies/{平台}.json` | 搜索/发布登录态 |
| API 密钥 | `~/.content-matrix/.env` | LLM / 微信 / 飞书 API |
| 用户配置 | `~/.content-matrix/config.json` | 默认 vault、后端选择等 |
| 更新缓存 | `~/.content-matrix/cache/update-check.cache` | 框架版本检查缓存 |
| 采集进度 | `~/.content-matrix/cache/feishu-export-progress.json` | 飞书导出断点续传 |
