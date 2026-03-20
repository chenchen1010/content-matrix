# 抖音发布

基于 [Stagehand](https://github.com/browserbasehq/stagehand) + Playwright 的抖音自动发布。

## 功能

- 自动上传视频到抖音创作者平台
- 自动填写描述/标题
- 持久化浏览器登录态，免重复扫码

## 前置依赖

```bash
cd skills/tools && npm install
```

需要 `.env` 配置 LLM API Key（见项目根目录 `.env.example`）。

## 用法

```bash
# 基本发布
node skills/tools/publish/douyin/publish-dy.mjs \
  --video=/path/to/video.mp4

# 带描述和标题
node skills/tools/publish/douyin/publish-dy.mjs \
  --video=/path/to/video.mp4 \
  --desc="#话题1 #话题2 描述文字" \
  --title="视频标题"
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--video=<路径>` | 是 | 视频文件路径 |
| `--desc=<描述>` | 否 | 视频描述 |
| `--title=<标题>` | 否 | 视频标题 |

## 登录

首次运行会弹出浏览器，需用抖音 App 扫码登录。登录态保存在 `~/.douyin-publish/chrome-data/`，后续自动复用。

Cookie 过期时重新运行会自动提示扫码。

## 排错

- **浏览器没弹出**：检查是否有其他 Chromium 进程占用，`killall Chromium` 后重试
- **描述没正确填写**：抖音编辑器 DOM 可能更新，脚本会自动回退到 AI 辅助操作
- **上传超时**：大文件上传较慢，脚本最多等 5 分钟
