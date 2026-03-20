# 抖音工具

抖音搜索 + 视频解析 + 语音识别（ASR）。

## 功能

- **搜索**：douyin_mcp 按关键词搜索视频（需 Cookie，Python 3.14+）
- **视频解析**：解析分享链接 → 无水印下载链接、标题、元数据
- **语音转文字**：从视频中提取口播文案（支持火山引擎 / 阿里云 ASR）
- **字幕下载**：通过 yt-dlp 下载自动生成的字幕
- 支持分享短链（`https://v.douyin.com/xxx/`）

## ASR 引擎

| 引擎 | 提供商 | 环境变量 | 特点 |
|------|--------|----------|------|
| `volcengine` | 火山引擎（字节跳动） | `VOLCENGINE_APP_ID` + `VOLCENGINE_ACCESS_TOKEN` | 抖音同源技术，推荐 |
| `dashscope` | 阿里云 DashScope | `DASHSCOPE_API_KEY` | qwen3-asr-flash 模型 |

通过 `.env` 中的 `ASR_PROVIDER` 切换引擎。

## 安装

### 1. 基础工具

```bash
# yt-dlp（视频元数据 / 字幕下载）
brew install yt-dlp

# douyin-mcp-server（MCP 服务，含视频解析 + ASR）
pip install douyin-mcp-server
```

### 2. 配置抖音搜索 Cookie（douyin_search 需要）

**方式一：登录助手（推荐，和小红书一样）**

```bash
./skills/tools/search/douyin/douyin-login.sh
```

1. 浏览器打开 `douyin.com`，在窗口内完成登录（扫码或密码）。  
2. 登录成功后脚本会**自动**检测（与 `douyin_search` 使用同一套接口校验）、保存 Cookie 并关闭浏览器，**无需在终端按 Enter**（与小红书 `xiaohongshu-login` 体验一致）。

**方式二：手动复制**

1. 浏览器访问 https://www.douyin.com 并登录
2. F12 → Application → Cookies → 复制全部
3. 粘贴到 `skills/tools/search/douyin/douyin_mcp/cookies.txt`

### 3. 配置 ASR（视频转文字）

在 `content-matrix/.env` 中填写：

```env
# 选择引擎: volcengine 或 dashscope
ASR_PROVIDER=volcengine

# 火山引擎
VOLCENGINE_APP_ID=你的APP_ID
VOLCENGINE_ACCESS_TOKEN=你的Access_Token

# 或阿里云
# DASHSCOPE_API_KEY=sk-xxx
```

**火山引擎开通步骤**：
1. 访问 [火山引擎语音识别控制台](https://console.volcengine.com/speech/service/8)
2. 开通「大模型语音识别」服务
3. 创建应用 → 记下 APP ID
4. 在应用详情中生成 Access Token

### 4. 注册 MCP 服务器

```bash
# 视频解析 + ASR（douyin）
mcporter config add douyin --command "python3" --arg "$(pwd)/skills/tools/search/douyin/start_server.py" --transport stdio --scope project

# 抖音搜索（douyin_search，需先配置 cookies.txt）
mcporter config add douyin_search --command "uv" \
  --arg "run" --arg "--directory=$(pwd)/skills/tools/search/douyin/douyin_mcp" \
  --arg "python" --arg "main.py" --transport stdio --scope project
```

## 用法

### MCP 方式（推荐）

```bash
# === 搜索（douyin_search，需 Cookie）===
mcporter call 'douyin_search.search_videos(keyword: "成人夜校", count: 20, sort_type: 1)'
mcporter call 'douyin_search.get_video_detail(aweme_id: "7590719110745525567")'

# === 解析 + ASR（douyin）===
mcporter call 'douyin.parse_douyin_video_info(share_link: "https://v.douyin.com/xxx/")'
mcporter call 'douyin.get_douyin_download_link(share_link: "https://v.douyin.com/xxx/")'
mcporter call 'douyin.extract_douyin_text(share_link: "https://v.douyin.com/xxx/")'
```

### yt-dlp 方式

```bash
yt-dlp --dump-json "https://v.douyin.com/xxx/"
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh" \
  --skip-download -o "/tmp/%(id)s" "https://v.douyin.com/xxx/"
```

### 搜索降级策略（topic-scout）

1. **Level 1**：douyin_search.search_videos（需 Cookie）
2. **Level 2**：Jina Reader
3. **Level 3**：cursor-ide-browser 浏览器

## 文件说明

| 文件/目录 | 说明 |
|------|------|
| `start_server.py` | 增强版 MCP 服务器入口（支持双 ASR 引擎） |
| `volcengine_asr.py` | 火山引擎 ASR 实现 |
| `douyin_mcp/` | 抖音搜索 MCP（需 Cookie，Python 3.14+） |
| `install.sh` | 安装 yt-dlp + douyin_mcp |

## 搜索后转口播文案（ASR）

`douyin_search` 只负责**搜视频列表**；口播转文字走 **`douyin` MCP** 的 `extract_douyin_text`（需配置 `.env` 里火山/阿里云 ASR）。

**推荐流程（由 AI 或脚本串联）：**

1. **搜索**  
   `mcporter call 'douyin_search.search_videos(keyword: "杭州夜校", count: 5)'`  
   在返回的 `data` 里取每条视频的 `aweme_id`（字段名以实际 JSON 为准，常见为 `aweme.aweme_id` 或顶层 `aweme_id`）。

2. **取可解析的分享链**  
   `mcporter call 'douyin_search.get_video_detail(aweme_id: "你的ID")'`  
   用返回里 `video.aweme_url`；若为空，可试 `https://www.douyin.com/video/{aweme_id}`。

3. **ASR 转录**  
   `mcporter call 'douyin.extract_douyin_text(share_link: "https://v.douyin.com/xxx/ 或上一步链接")'`  
   成功则返回口播全文，可写入 Obsidian「爆款参考」等。

批量时：对 Top N 条循环步骤 2–3，注意接口频率与 ASR 计费。

## 排错

- **登录脚本跑很久不关浏览器**：已增强 Cookie 合并、UA 与 MCP 一致、`is_session_usable`（history 或搜索任一通即成功）；仍卡住时看终端是否在打点，或 45s 后走页面「个人主页」链路的备用保存。
- **终端不结束**：脚本结束时会 `process.exit(0)`；若仍挂住，多半是别的进程占着终端。
- **ASR 报错 "未设置 xxx"**：检查 `.env` 中的 `ASR_PROVIDER` 和对应密钥
- **412 错误**：yt-dlp 被 IP 限制，用 `--cookies-from-browser chrome`
- **分享链接解析失败**：确认链接有效，部分链接可能已过期
- **火山引擎连接超时**：检查网络，确认服务已开通
