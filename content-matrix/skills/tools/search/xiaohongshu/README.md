# 小红书工具

基于 [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 的小红书搜索、详情获取、内容发布。

## 功能

- `search_feeds` — 按关键词搜索笔记
- `get_feed_detail` — 获取单条笔记完整详情（正文、图片、视频、评论、互动数据）
- `publish_content` — 发布图文/视频到小红书
- `check_login_status` — 检查登录状态
- 共 12 个工具，完整列表运行 `mcporter call xiaohongshu.list_tools`

## 安装

### 方式一：从 Release 下载编译好的 binary（推荐）

```bash
# macOS ARM (M1/M2/M3)
curl -L https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-arm64.tar.gz | tar xz
chmod +x xiaohongshu-mcp xiaohongshu-login

# macOS Intel
curl -L https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-amd64.tar.gz | tar xz

# Linux
curl -L https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-linux-amd64.tar.gz | tar xz
```

### 方式二：Docker

```bash
docker run -d -p 18060:18060 xpzouying/xiaohongshu-mcp
```

### 方式三：从源码编译

```bash
git clone https://github.com/xpzouying/xiaohongshu-mcp.git
cd xiaohongshu-mcp
go build -o xiaohongshu-mcp .
go build -o xiaohongshu-login ./cmd/login/
```

## 启动

```bash
# 1. 先登录（首次 or Cookie 过期时）
./xiaohongshu-login
# 浏览器会打开，扫码登录后 Cookie 自动保存到 ./cookies.json

# 2. 启动 MCP 服务
./xiaohongshu-mcp
# 默认监听 http://localhost:18060/mcp
```

## 注册到 Cursor / Claude

在项目的 `.cursor/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "xiaohongshu": {
      "url": "http://localhost:18060/mcp",
      "description": "小红书 MCP 服务"
    }
  }
}
```

## 调用示例

```bash
# 搜索
mcporter call 'xiaohongshu.search_feeds(keyword: "成人夜校")'

# 获取详情（需要 xsec_token，从搜索结果中获取）
mcporter call 'xiaohongshu.get_feed_detail(feed_id: "66ad93e6xxx", xsec_token: "ABxxx")'

# 获取详情 + 全部评论
mcporter call 'xiaohongshu.get_feed_detail(feed_id: "66ad93e6xxx", xsec_token: "ABxxx", load_all_comments: true)'

# 发布
mcporter call 'xiaohongshu.publish_content(title: "标题", content: "正文", images: ["/path/img.jpg"], tags: ["tag"])'
```

## 链接格式

小红书笔记的可访问链接必须带 `xsec_token`：
```
https://www.xiaohongshu.com/explore/{noteId}?xsec_token={xsecToken}&xsec_source=pc_feed
```

不带 token 的链接打不开。`xsec_token` 从 `search_feeds` 的返回结果中获取。

## 排错

- **Cookie 过期**：重新运行 `./xiaohongshu-login` 扫码
- **端口被占用**：`lsof -i :18060` 检查，或改用其他端口
- **搜索没结果**：检查 `check_login_status`，确认已登录
- 更多问题见 [疑难杂症](https://github.com/xpzouying/xiaohongshu-mcp/issues/56)
