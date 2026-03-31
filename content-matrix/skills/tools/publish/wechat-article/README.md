# 公众号发布

支持两种发布形式：

| 类型 | 参数 | 微信API | 说明 |
|------|------|---------|------|
| **文章** | `--markdown` | `article_type: news` | Markdown → 文颜排版 → HTML 图文消息 |
| **小绿书** | `--image-dir` | `article_type: newspic` | 图片目录 → 图片消息（最多20张） |

> 公众号与视频号是微信生态下的两个独立产品。公众号发布文章，视频号发布短视频。

## 配置

在 `content-matrix/.env` 中配置：

```env
WECHAT_APP_ID=wx...
WECHAT_APP_SECRET=...
EVOLINK_API_KEY=...    # 封面生成（可选，仅文章模式）
```

## 用法

### 小绿书（图片消息）

把一组图片发布为公众号"小绿书"格式。图片按文件名排序，首张图自动成为封面。

```bash
python3 publish.py \
  --app-id $WECHAT_APP_ID \
  --app-secret $WECHAT_APP_SECRET \
  --title "标题" \
  --image-dir /path/to/images/ \
  --type 小绿书
```

- 支持 jpg/jpeg/png/gif/webp
- 最多 20 张图片
- 图片上传为永久素材

### 文章（图文消息）

#### 从 Markdown 发布

```bash
python3 publish.py \
  --app-id $WECHAT_APP_ID \
  --app-secret $WECHAT_APP_SECRET \
  --markdown /path/to/article.md \
  --author "作者名"
```

#### 从图片目录发布为文章

图片嵌入 HTML 正文，作为图文消息发布（与小绿书的区别是呈现形式不同）。

```bash
python3 publish.py \
  --app-id $WECHAT_APP_ID \
  --app-secret $WECHAT_APP_SECRET \
  --title "标题" \
  --image-dir /path/to/images/ \
  --type 文章
```

## 文章模式流程

1. 读取 Markdown 文件
2. 调用文颜 MCP 进行排版美化
3. 调用 Evolink 生成封面图（可选）
4. 上传到微信公众号草稿箱

## 参考文档

- `references/wenyan-guide.md` — 文颜排版使用指南
- `references/api-guide.md` — 微信公众号 API 参考
- [新增草稿 API](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add.html)

## 远程 API 模式

通过远程 API 服务器发布，无需本地配置 AppID/AppSecret，IP 白名单在服务器端配置。

### 小绿书（远程）

```bash
python3 publish.py \
  --remote https://cs.qwjxqn.xyz/wechat-mp \
  --api-token $WECHAT_MP_API_TOKEN \
  --account jscxbwd \
  --title "标题" \
  --image-dir /path/to/images/ \
  --type 小绿书
```

### 文章（远程）

```bash
python3 publish.py \
  --remote https://cs.qwjxqn.xyz/wechat-mp \
  --api-token $WECHAT_MP_API_TOKEN \
  --account jscxbwd \
  --title "标题" \
  --image-dir /path/to/images/ \
  --type 文章
```

支持的账号：`default`、`qwjxqn`、`jscxbwd`

## 排错

- **AccessToken 获取失败** — 检查 AppID/AppSecret，确认 IP 白名单
- **文颜排版失败** — 确认 `@wenyan-md/mcp` 已安装：`npx @wenyan-md/mcp --help`
- **小绿书超过 20 张** — 自动截断为前 20 张，会打印警告
