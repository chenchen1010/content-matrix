# 视频号发布

基于 Stagehand + Playwright，自动上传视频、填写描述、声明原创到微信视频号。

> 视频号与公众号是微信生态下的两个独立产品，发布流程不同。

## 前置依赖

```bash
cd skills/tools && npm install
```

## 用法

```bash
node skills/tools/publish/wechat-channels/publish-sph.mjs \
  --video=/path/to/video.mp4 \
  --desc="#话题 描述文字" \
  --original
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--video=<路径>` | 是 | 视频文件路径 |
| `--desc=<描述>` | 否 | 视频描述 |
| `--original` | 否 | 声明原创 |
| `--no-original` | 否 | 不声明原创 |

## 登录

首次弹出浏览器需微信扫码登录**视频号**后台。登录态保存在 `~/.wechat-channels-publish/chrome-data/`。

> 注意：视频号后台与公众号后台是分开的，扫码时确认进入的是视频号。

## 排错

- **扫码后没反应** — 确认扫的是微信视频号后台，不是公众号
- **iframe 穿透失败** — 视频号后台用 wujie 微前端，DOM 在 `iframe[name="content"]` 中，脚本已处理
