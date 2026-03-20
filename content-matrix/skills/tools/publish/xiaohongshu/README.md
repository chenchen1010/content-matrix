# 小红书发布

小红书的发布能力已集成在 xiaohongshu-mcp 中，和搜索/详情共用同一个 MCP 服务。

> 不需要单独的发布脚本。启动 xiaohongshu-mcp 后即可搜索+发布。

## 前置条件

xiaohongshu-mcp 服务已启动（见 `skills/tools/search/xiaohongshu/README.md`）。

## 发布调用

```bash
mcporter call 'xiaohongshu.publish_content(title: "标题", content: "正文描述", images: ["/path/img1.jpg", "/path/img2.jpg"], tags: ["标签1", "标签2"])'
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `title` | 是 | 笔记标题 |
| `content` | 是 | 正文描述 |
| `images` | 是 | 图片路径数组（本地绝对路径或 HTTP URL） |
| `tags` | 否 | 标签数组 |

## 图片说明

支持两种输入：
- **本地路径**（推荐）：`["/Users/xxx/img.jpg"]`
- **HTTP URL**：`["https://example.com/img.jpg"]`

本地路径更稳定，避免远程图片下载超时。

## 注意事项

- 发布前确保已登录（`check_login_status`）
- 小红书对发布频率有限制，矩阵发布注意控制节奏
- 图文笔记至少需要 1 张图片
