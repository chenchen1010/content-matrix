# 公众号工具

> 公众号与视频号是微信生态下的两个独立产品。本目录仅服务**公众号文章**的搜索与阅读。视频号无搜索工具（短视频平台，类似抖音）。

两个独立组件：搜索 + 阅读。

## 组件 1: 搜索公众号文章 — miku_ai

[miku_ai](https://pypi.org/project/miku-ai/) 提供公众号文章搜索能力。

### 安装

```bash
pip install miku-ai
```

### 用法

```python
import asyncio
from miku_ai import get_wexin_article

async def search():
    results = await get_wexin_article("成人夜校", 10)
    for a in results:
        print(f'{a["title"]} | {a["url"]}')

asyncio.run(search())
```

命令行快捷调用：
```bash
python3 -c "
import asyncio
from miku_ai import get_wexin_article
async def s():
    for a in await get_wexin_article('成人夜校', 10):
        print(f'{a[\"title\"]} | {a[\"url\"]}')
asyncio.run(s())
"
```

## 组件 2: 阅读公众号文章 — wechat-article-for-ai (Camoufox)

> ⚠️ 微信文章有反爬机制，Jina Reader 和 curl **读不了**。必须用 Camoufox（反检测浏览器）。

### 安装

```bash
cd skills/tools/search/wechat/wechat-article-for-ai
pip install -r requirements.txt
# 首次运行会自动下载 Camoufox 浏览器
```

### 用法

```bash
# 单篇文章
python3 main.py "https://mp.weixin.qq.com/s/ARTICLE_ID"

# 批量（从文件读取 URL）
python3 main.py -f urls.txt -o ./output -v

# 遇到验证码时，用 --no-headless 显示浏览器手动处理
python3 main.py --no-headless "https://mp.weixin.qq.com/s/ARTICLE_ID"
```

### 输出

```
output/
  <文章标题>/
    <文章标题>.md    # Markdown（含 YAML frontmatter）
    images/
      img_001.png
      ...
```

### 作为 MCP 服务运行

```bash
python3 mcp_server.py
```

MCP 配置：
```json
{
  "mcpServers": {
    "wechat-to-md": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "cwd": "skills/tools/search/wechat/wechat-article-for-ai"
    }
  }
}
```

## 排错

- **搜索没结果**：miku_ai 依赖第三方接口，偶尔不稳定，等几分钟重试
- **文章读取为空**：微信限流，等几分钟。或用 `--no-headless` 手动过验证码
- **Camoufox 下载失败**：检查网络，可能需要代理
