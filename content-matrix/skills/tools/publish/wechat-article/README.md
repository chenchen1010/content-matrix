# 公众号发布

完整的公众号文章发布流水线：Markdown → 文言排版 → Evolink 封面 → 微信草稿。

> 公众号与视频号是微信生态下的两个独立产品。公众号发布文章，视频号发布短视频。

## 前置依赖

```bash
# 文言排版 MCP
npm install -g @wenyan-md/mcp

# Python 依赖
pip install requests
```

## 配置

在 `content-matrix/.env` 中配置：

```env
WECHAT_APP_ID=wx...
WECHAT_APP_SECRET=...
EVOLINK_API_KEY=...    # 封面生成（可选）
```

## 用法

```bash
python3 skills/tools/publish/wechat-article/publish.py \
  --input=/path/to/article.md \
  --title="文章标题" \
  --author="作者名"
```

## 流程

1. 读取 Markdown 文件
2. 调用文言 MCP 进行排版美化
3. 调用 Evolink 生成封面图（可选）
4. 上传到微信公众号草稿箱

## 参考文档

- `references/wenyan-guide.md` — 文言排版使用指南
- `references/api-guide.md` — 微信公众号 API 参考

## 排错

- **AccessToken 获取失败** — 检查 AppID/AppSecret，确认 IP 白名单
- **文言排版失败** — 确认 `@wenyan-md/mcp` 已安装：`npx @wenyan-md/mcp --help`
