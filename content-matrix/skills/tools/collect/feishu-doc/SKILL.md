---
name: feishu-doc-to-markdown
description: Export Feishu/Lark cloud document links to local Markdown files with local images by reusing a logged-in Chrome session and reading Feishu's runtime block model.
---

# 飞书文档转 Markdown

## 功能

将飞书/Lark 的 `docx` 或 `wiki` 链接导出为本地 Markdown 文件，同时下载图片到本地。

优先读取飞书页面运行时的文档块模型（`window.PageMain.blockManager.rootBlockModel`），比普通 DOM 抓取更完整。当运行时模型不可用时，自动回退到 HTML 提取。

## 依赖安装

```bash
python3.11 -m pip install playwright markdownify
python3.11 -m playwright install chromium
```

## 用法

### 导出单个链接

```bash
python3.11 content-matrix/skills/tools/collect/feishu-doc/scripts/export_feishu_doc_to_md.py 'https://my.feishu.cn/wiki/XXXX'
```

### 批量导出

在 `content-matrix/skills/tools/collect/feishu-doc/` 下新建 `links.txt`，每行一个飞书链接，然后运行：

```bash
python3.11 content-matrix/skills/tools/collect/feishu-doc/scripts/export_feishu_doc_to_md.py
```

## 输出

默认输出到用户数据目录（不在框架目录内）：

- Markdown 文件：`~/.content-matrix/downloads/feishu-doc/<文档标题>/<文档标题>.md`
- 图片文件：`~/.content-matrix/downloads/feishu-doc/<文档标题>/images/`
- 进度文件：`~/.content-matrix/cache/feishu-export-progress.json`（支持断点续传）

可通过 `--output` 参数指定其他输出目录（如 Obsidian vault）：

```bash
python3.11 scripts/export_feishu_doc_to_md.py --output ~/Desktop/黑曜石/夜校/素材库/3-行业知识 'https://my.feishu.cn/wiki/XXXX'
```

## 首次运行

脚本会启动一个专用的 Chrome 调试窗口（端口 9222，profile 保存在 `~/.chrome-debug-profile`）。

- 首次需在弹出的 Chrome 窗口中登录飞书
- 登录态保存在专用 profile 中，后续无需重复登录

## 故障排查

- 找不到 Chrome → 设置环境变量 `CDC_CHROME_PATH`
- 页面要求登录 → 在 debug Chrome 窗口完成登录后重新运行
- 只导出了部分内容 → 检查 `PageMain` 是否存在，参考 [runtime-model-notes.md](references/runtime-model-notes.md)

## 资源

- `scripts/export_feishu_doc_to_md.py` — 主导出脚本
- `references/runtime-model-notes.md` — 运行时模型原理说明
