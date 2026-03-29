#!/usr/bin/env python3.11
"""
Export Feishu/Lark doc or wiki links to local Markdown files.

This script reuses a dedicated Chrome profile, connects to the logged-in
browser over the debug port, reads Feishu's runtime block model, and writes
Markdown plus local images.

Usage:
  python3.11 scripts/export_feishu_doc_to_md.py
  python3.11 scripts/export_feishu_doc_to_md.py links.txt
  python3.11 scripts/export_feishu_doc_to_md.py https://my.feishu.cn/wiki/xxxx
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import random
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from markdownify import markdownify as md
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# 配置
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_LINKS_FILE = SKILL_DIR / "links.txt"
LEGACY_LINKS_FILE = SKILL_DIR / "链接.txt"

# 默认输出到用户数据目录，不污染框架目录
_USER_DATA_DIR = Path.home() / ".content-matrix"
OUTPUT_DIR = _USER_DATA_DIR / "downloads" / "feishu-doc"
PROGRESS_FILE = _USER_DATA_DIR / "cache" / "feishu-export-progress.json"
DELAY_MIN = 3  # 每个文档间最小延迟（秒）
DELAY_MAX = 6  # 每个文档间最大延迟（秒）
PAGE_LOAD_TIMEOUT = 60000  # 页面加载超时（毫秒）
MAX_RETRIES = 2
CDP_PORT = 9222

# 专用 debug Chrome profile（与用户日常 Chrome 完全隔离）
DEBUG_PROFILE_DIR = Path.home() / ".chrome-debug-profile"


def detect_chrome_executable() -> str:
    """尽量自动找到本机 Chrome 可执行文件"""
    env_path = os.environ.get("CDC_CHROME_PATH")
    candidates = [
        env_path,
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/opt/google/chrome/chrome",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path

    for binary in ["google-chrome", "chromium", "chromium-browser", "chrome"]:
        found = shutil.which(binary)
        if found:
            return found

    raise FileNotFoundError(
        "未找到 Chrome。请安装 Google Chrome，或设置环境变量 CDC_CHROME_PATH。"
    )


def read_links(file_path: Path) -> list[str]:
    """读取链接文件，一行一个 URL"""
    lines = file_path.read_text(encoding="utf-8").strip().splitlines()
    links = [line.strip() for line in lines if line.strip() and line.strip().startswith("http")]
    return links


def extract_doc_token(url: str) -> str:
    """从 URL 中提取文档 token（最后一段路径）"""
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1]


def load_progress() -> set:
    """加载已完成的 URL 集合"""
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        return set(data.get("completed", []))
    return set()


def save_progress(completed: set):
    """保存进度"""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(
        json.dumps({"completed": list(completed)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_login_page(url: str) -> bool:
    """判断是否在登录页"""
    login_keywords = ["login", "passport", "accounts", "sign-in", "auth"]
    return any(kw in url.lower() for kw in login_keywords)


def launch_debug_chrome(first_url: str):
    """启动专用 debug Chrome（独立 profile，不影响用户日常 Chrome）"""
    import socket

    # 检查 debug 端口是否已经在用
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1)
        sock.connect(("127.0.0.1", CDP_PORT))
        sock.close()
        print(f"✅ debug Chrome 已在运行（端口 {CDP_PORT}）")
        return
    except (ConnectionRefusedError, OSError):
        sock.close()

    DEBUG_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    is_first_time = not (DEBUG_PROFILE_DIR / "Default").exists()

    print(f"🔄 启动专用 debug Chrome（profile: {DEBUG_PROFILE_DIR}）...")
    chrome_executable = detect_chrome_executable()
    subprocess.Popen(
        [
            chrome_executable,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={DEBUG_PROFILE_DIR}",
            first_url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 等待端口就绪
    for _ in range(30):
        time.sleep(1)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(("127.0.0.1", CDP_PORT))
            sock.close()
            print("✅ debug Chrome 已启动")
            if is_first_time:
                print("\n" + "=" * 50)
                print("⚠️  首次运行，请在弹出的 Chrome 中登录飞书")
                print("   （登录态会保存在专用 profile 中，下次无需再登录）")
                print("=" * 50)
            return
        except (ConnectionRefusedError, OSError):
            sock.close()

    print("❌ 无法启动 debug Chrome")
    sys.exit(1)


def ensure_login(playwright, first_url: str) -> tuple:
    """通过 CDP 连接到 debug Chrome，返回 (browser, context)"""
    launch_debug_chrome(first_url)

    print("🔄 连接到 debug Chrome...")
    browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
    context = browser.contexts[0]
    print("✅ 已连接")

    # 验证登录态
    page = context.new_page()
    page.goto(first_url, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
    time.sleep(5)

    if not is_login_page(page.url):
        print("✅ 登录态有效")
        page.close()
        return browser, context

    # 需要登录
    print("\n" + "=" * 50)
    print("⚠️  请在 debug Chrome 中登录飞书")
    print("   登录完成后脚本会自动继续...")
    print("=" * 50)

    for _ in range(600):
        time.sleep(1)
        try:
            if not is_login_page(page.url):
                time.sleep(3)
                if not is_login_page(page.url):
                    break
        except Exception:
            pass
    else:
        print("❌ 登录超时")
        browser.close()
        sys.exit(1)

    print("✅ 登录成功（已保存到专用 profile，下次无需再登录）")
    page.close()
    return browser, context


def scroll_to_load(page):
    """滚动页面触发懒加载，支持飞书文档的内部滚动容器"""
    page.evaluate("""
        async () => {
            const delay = ms => new Promise(r => setTimeout(r, ms));

            // 飞书文档的滚动容器通常不是 document 本身，而是内部的一个 div
            // 尝试找到实际的滚动容器
            function findScrollContainer() {
                const candidates = [
                    document.querySelector('.doc-content-container'),
                    document.querySelector('.wiki-content-container'),
                    document.querySelector('[class*="render-unit-wrapper"]'),
                    document.querySelector('[data-content-editable-root]'),
                    document.querySelector('.docx-container'),
                    document.querySelector('.main-content'),
                ];
                for (const el of candidates) {
                    if (el && el.scrollHeight > el.clientHeight) return el;
                }

                // 兜底：找页面中 scrollHeight 最大的可滚动元素
                let best = null;
                let maxScroll = 0;
                for (const el of document.querySelectorAll('div')) {
                    const style = window.getComputedStyle(el);
                    const overflow = style.overflowY;
                    if ((overflow === 'auto' || overflow === 'scroll' || overflow === 'overlay')
                        && el.scrollHeight > el.clientHeight + 100
                        && el.scrollHeight > maxScroll
                        && el.clientWidth > 300) {
                        maxScroll = el.scrollHeight;
                        best = el;
                    }
                }
                return best || document.documentElement;
            }

            const container = findScrollContainer();

            // 多轮滚动：飞书会在滚动时动态渲染新内容，导致 scrollHeight 增长
            let prevHeight = 0;
            let stableCount = 0;
            for (let round = 0; round < 10; round++) {
                const totalHeight = container.scrollHeight;
                let currentPos = 0;
                const step = Math.max(container.clientHeight - 50, 300);

                while (currentPos < totalHeight) {
                    container.scrollTop = currentPos;
                    await delay(250);
                    currentPos += step;
                }
                // 滚到最底部确保触发
                container.scrollTop = container.scrollHeight;
                await delay(500);

                const newHeight = container.scrollHeight;
                if (newHeight === prevHeight) {
                    stableCount++;
                    if (stableCount >= 2) break;
                } else {
                    stableCount = 0;
                }
                prevHeight = newHeight;
            }

            // 滚回顶部
            container.scrollTop = 0;
        }
    """)


def get_doc_title(page) -> str:
    """尝试获取文档标题"""
    selectors = [
        ".doc-title",
        "[data-block-type='title']",
        ".wiki-title",
        "h1",
        "#doctitle",
    ]
    for sel in selectors:
        el = page.query_selector(sel)
        if el:
            text = el.inner_text().strip()
            if text:
                # 清理文件名中的非法字符
                return re.sub(r'[\\/:*?"<>|]', "_", text)[:100]
    return ""


def extract_iframe_content(page) -> str:
    """提取页面中 iframe 的内容（飞书智能纪要等文档的正文在 iframe 中）"""
    iframe_htmls = []
    frames = page.frames

    for frame in frames:
        if frame == page.main_frame:
            continue
        if frame.url == "about:blank":
            continue

        try:
            # 等待 frame 内容加载
            frame.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass

        try:
            # 在 iframe 中滚动以触发懒加载
            frame.evaluate("""
                async () => {
                    const delay = ms => new Promise(r => setTimeout(r, ms));
                    const container = document.scrollingElement || document.documentElement || document.body;
                    if (!container || container.scrollHeight <= container.clientHeight + 50) return;
                    let prevH = 0;
                    for (let round = 0; round < 10; round++) {
                        let pos = 0;
                        const step = Math.max(window.innerHeight || 400, 200);
                        while (pos < container.scrollHeight) {
                            container.scrollTop = pos;
                            window.scrollTo(0, pos);
                            await delay(200);
                            pos += step;
                        }
                        container.scrollTop = container.scrollHeight;
                        window.scrollTo(0, container.scrollHeight);
                        await delay(300);
                        if (container.scrollHeight === prevH) break;
                        prevH = container.scrollHeight;
                    }
                    container.scrollTop = 0;
                    window.scrollTo(0, 0);
                }
            """)
        except Exception:
            pass

        try:
            body = frame.query_selector("body")
            if not body:
                continue
            text = body.inner_text()
            html = body.inner_html()
            print(f"  📦 frame [{frame.url[:60]}]: text={len(text)} html={len(html)}")
            if text:
                print(f"     内容预览: {text[:150]}")
            if len(text) > 20:
                iframe_htmls.append((len(text), html))
        except Exception as e:
            print(f"  ⚠️  frame 访问失败: {e}")

    if iframe_htmls:
        iframe_htmls.sort(key=lambda x: x[0], reverse=True)
        combined = "\n".join(html for _, html in iframe_htmls)
        return combined
    return ""


def extract_content_html(page) -> str:
    """提取文档主体 HTML，支持 iframe 内容"""
    # 飞书文档可能使用的内容容器选择器（按优先级）
    selectors = [
        "[data-content-editable-root]",
        ".doc-block-container",
        ".docx-container",
        ".wiki-content",
        ".doc-content",
        ".lark-doc-block",
        "article",
        ".main-content",
        "#content",
    ]

    best_html = ""
    for sel in selectors:
        els = page.query_selector_all(sel)
        for el in els:
            try:
                html = el.inner_html()
                if len(html) > len(best_html):
                    best_html = html
            except Exception:
                pass

    # 同时尝试从 iframe 中提取内容
    iframe_html = extract_iframe_content(page)

    # 如果 iframe 内容更丰富，合并或替换
    if len(iframe_html) > len(best_html):
        if len(best_html) > 100:
            return best_html + "\n" + iframe_html
        return iframe_html

    if len(best_html) > 100:
        return best_html

    # 兜底：找到页面中 innerText 最长的内容块
    result = page.evaluate("""
        () => {
            const candidates = document.querySelectorAll('div[class]');
            let best = null;
            let maxLen = 0;
            for (const el of candidates) {
                const text = el.innerText || '';
                if (text.length > maxLen && text.length > 200) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 400) {
                        maxLen = text.length;
                        best = el;
                    }
                }
            }
            return best ? best.innerHTML : '';
        }
    """)
    return result


def cleanup_markdown(markdown: str) -> str:
    """统一清理 Markdown 文本"""
    markdown = markdown.replace("\u200b", "")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = re.sub(r" +\n", "\n", markdown)
    return markdown.strip() + "\n"


def extract_runtime_model(page) -> dict | None:
    """参考 cloud-document-converter，读取飞书运行时文档块模型"""
    script = r"""
        async () => {
            function resolveMentionText(uid) {
                if (!uid) return null;
                const selectors = [
                    `a[data-token="${uid}"]`,
                    `[data-token="${uid}"]`,
                    `[data-lark-user-id="${uid}"]`,
                ];
                for (const selector of selectors) {
                    const el = document.querySelector(selector);
                    const text = (el?.innerText || el?.textContent || '').trim();
                    if (text) {
                        return text.startsWith('@') ? text : '@' + text;
                    }
                }
                return null;
            }

            function buildImageUrl(token, recordId) {
                const host = window.globalConfig?.drive_api?.[0];
                if (!host || !token || !recordId) return null;
                const url = new URL(`https://${host}/space/api/box/stream/download/all/${token}/`);
                url.searchParams.set('mount_node_token', recordId);
                url.searchParams.set('mount_point', 'docx_image');
                return url.toString();
            }

            function buildFileUrl(token, recordId) {
                const host = window.globalConfig?.drive_api?.[0];
                if (!host || !token || !recordId) return null;
                const url = new URL(`https://${host}/space/api/box/stream/download/all/${token}/`);
                url.searchParams.set('mount_node_token', recordId);
                url.searchParams.set('mount_point', 'docx_file');
                const hostToken = window.location.pathname.split('/').filter(Boolean).at(-1) || '';
                if (hostToken) {
                    url.searchParams.set('synced_block_host_token', hostToken);
                    url.searchParams.set('synced_block_host_type', '22');
                }
                return url.toString();
            }

            function serializeOps(ops) {
                return (ops || []).map(op => {
                    const attributes = op?.attributes || {};
                    let mentionText = null;
                    if (attributes['inline-component']) {
                        try {
                            const inlineComponent = JSON.parse(attributes['inline-component']);
                            mentionText = resolveMentionText(inlineComponent?.data?.uid);
                        } catch (error) {
                            mentionText = null;
                        }
                    }
                    return {
                        insert: typeof op?.insert === 'string' ? op.insert : '',
                        attributes: {
                            bold: attributes.bold || null,
                            italic: attributes.italic || null,
                            strikethrough: attributes.strikethrough || null,
                            underline: attributes.underline || null,
                            inlineCode: attributes.inlineCode || null,
                            link: attributes.link || null,
                            mentionText,
                        },
                    };
                });
            }

            function serializeBlock(block) {
                if (!block) return null;
                const snapshot = block.snapshot || {};
                return {
                    id: block.id,
                    type: block.type,
                    record_id: block.record?.id || null,
                    all_text: block.zoneState?.allText || '',
                    ops: serializeOps(block.zoneState?.content?.ops),
                    snapshot: {
                        type: snapshot.type || null,
                        seq: snapshot.seq || null,
                        seq_level: snapshot.seq_level || null,
                        done: snapshot.done || false,
                        block_type_id: snapshot.block_type_id || null,
                        image: snapshot.image ? {
                            token: snapshot.image.token || null,
                            name: snapshot.image.name || null,
                            caption: snapshot.image.caption?.text?.initialAttributedTexts?.text?.['0'] || '',
                            url: buildImageUrl(snapshot.image.token, block.record?.id || ''),
                        } : null,
                        file: snapshot.file ? {
                            token: snapshot.file.token || null,
                            name: snapshot.file.name || null,
                            url: buildFileUrl(snapshot.file.token, block.record?.id || ''),
                        } : null,
                    },
                    children: (block.children || []).map(serializeBlock).filter(Boolean),
                };
            }

            const root = window.PageMain?.blockManager?.rootBlockModel;
            if (!root) return null;

            return {
                page_title: (root.zoneState?.allText || '').trim(),
                root: serializeBlock(root),
            };
        }
    """
    try:
        return page.evaluate(script)
    except Exception as e:
        print(f"  ⚠️  运行时模型提取失败: {e}")
        return None


def apply_inline_marks(text: str, attrs: dict) -> str:
    """把飞书内联样式转成 Markdown"""
    if not text:
        return ""

    if attrs.get("mentionText"):
        text = attrs["mentionText"]

    if attrs.get("inlineCode"):
        text = f"`{text}`"
    if attrs.get("bold"):
        text = f"**{text}**"
    if attrs.get("italic"):
        text = f"*{text}*"
    if attrs.get("strikethrough"):
        text = f"~~{text}~~"
    if attrs.get("underline"):
        text = f"<u>{text}</u>"
    if attrs.get("link"):
        text = f"[{text}]({attrs['link']})"
    return text


def render_inline_ops(ops: list[dict]) -> str:
    parts = []
    for op in ops or []:
        insert = op.get("insert", "")
        if insert == "\n":
            continue
        attrs = op.get("attributes") or {}
        text = apply_inline_marks(insert, attrs)
        parts.append(text)
    result = "".join(parts).strip()
    return re.sub(r" {2,}", " ", result)


def render_quote_block(block: dict) -> str:
    children = []
    for child in block.get("children", []):
        rendered = render_block_markdown(child)
        if rendered:
            children.append(rendered)
    if not children:
        return ""
    lines = []
    for child in children:
        for line in child.splitlines():
            lines.append("> " if not line.strip() else f"> {line}")
    return "\n".join(lines)


def render_list_block(block: dict, indent: int = 0) -> str:
    text = render_inline_ops(block.get("ops", []))
    type_ = block.get("type")
    if type_ == "todo":
        checked = "x" if block.get("snapshot", {}).get("done") else " "
        prefix = f"{'  ' * indent}- [{checked}] "
    elif type_ == "ordered":
        seq = block.get("snapshot", {}).get("seq")
        prefix = f"{'  ' * indent}{seq if str(seq).isdigit() else '1'}. "
    else:
        prefix = f"{'  ' * indent}- "

    lines = [prefix + text if text else prefix.rstrip()]
    for child in block.get("children", []):
        rendered = render_block_markdown(child, indent=indent + 1)
        if rendered:
            lines.append(rendered)
    return "\n".join(lines)


def render_block_markdown(block: dict, indent: int = 0) -> str:
    type_ = block.get("type")
    if type_ == "page":
        parts = [render_block_markdown(child) for child in block.get("children", [])]
        return "\n\n".join(part for part in parts if part)

    if type_ == "quote_container":
        return render_quote_block(block)

    if type_ and type_.startswith("heading") and type_[-1].isdigit():
        depth = int(type_[-1])
        if 1 <= depth <= 6:
            text = render_inline_ops(block.get("ops", []))
            return f"{'#' * depth} {text}".strip()

    if type_ in {"text", "heading7", "heading8", "heading9"}:
        return render_inline_ops(block.get("ops", []))

    if type_ in {"bullet", "ordered", "todo"}:
        return render_list_block(block, indent=indent)

    if type_ == "image":
        image = block.get("snapshot", {}).get("image") or {}
        alt = (image.get("caption") or "").strip()
        url = image.get("url") or ""
        return f"{'  ' * indent}![{alt}]({url})" if url else ""

    if type_ == "file":
        file_data = block.get("snapshot", {}).get("file") or {}
        name = file_data.get("name") or "file"
        url = file_data.get("url") or ""
        rendered = f"[{name}]({url})" if url else name
        return f"{'  ' * indent}{rendered}"

    if type_ in {"whiteboard", "isv", "divider", "fallback"}:
        return ""

    parts = [render_block_markdown(child, indent=indent) for child in block.get("children", [])]
    return "\n\n".join(part for part in parts if part)


def extract_markdown_from_runtime_model(page) -> str:
    """优先用飞书运行时块模型导出 Markdown"""
    payload = extract_runtime_model(page)
    if not payload or not payload.get("root"):
        return ""
    markdown = render_block_markdown(payload["root"])
    return cleanup_markdown(markdown)


def download_images(markdown_text: str, doc_dir: Path, page=None) -> str:
    """下载 Markdown 中的图片到本地，替换链接。用 page 的 cookies 来下载需要认证的图片。"""
    img_dir = doc_dir / "images"
    img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    # 获取 cookies 用于认证图片下载
    cookie_header = ""
    if page:
        try:
            cookies = page.context.cookies()
            cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        except Exception:
            pass

    img_count = 0

    def replace_image(match):
        nonlocal img_count
        alt = match.group(1)
        url = match.group(2)
        if not url.startswith("http"):
            return match.group(0)

        img_dir.mkdir(parents=True, exist_ok=True)
        img_count += 1
        ext = ".png"
        url_path = urlparse(url).path
        if "." in url_path.split("/")[-1]:
            ext = "." + url_path.split("/")[-1].split(".")[-1]
        img_name = f"img_{img_count:03d}{ext}"
        img_path = img_dir / img_name

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Cookie": cookie_header,
                "Referer": "https://feishu.cn/",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                img_path.write_bytes(resp.read())
            return f"![{alt}](images/{img_name})"
        except Exception as e:
            print(f"  ⚠️  图片下载失败: {e}")
            return match.group(0)

    return img_pattern.sub(replace_image, markdown_text)


def export_single_doc(page, url: str) -> bool:
    """导出单个文档，返回是否成功"""
    doc_token = extract_doc_token(url)

    try:
        page.goto(url, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
    except PWTimeout:
        print(f"  ❌ 页面加载超时")
        return False

    # 等待内容渲染（长文档需要更多时间）
    time.sleep(5)

    # 检查是否有权限
    page_text = page.inner_text("body")
    if any(kw in page_text for kw in ["无权限", "没有权限", "无法访问", "申请权限"]):
        print(f"  ❌ 无权限访问")
        return False

    # 滚动主页面触发懒加载
    scroll_to_load(page)
    time.sleep(2)

    # 尝试展开折叠区域（飞书智能纪要的"总结"、"待办"等可能是折叠的）
    try:
        expand_results = page.evaluate("""
            () => {
                const clicked = [];
                // 查找 ISV block 容器中的展开按钮
                const expandSelectors = [
                    '[data-testid*="expand"]',
                    '[class*="expand"]',
                    '[class*="toggle"]',
                    '[class*="collapse"]',
                    '.isv-block-container',
                    '[class*="summary"]',
                    '[class*="fold"]',
                ];
                for (const sel of expandSelectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        if (el.offsetHeight > 0) {
                            clicked.push(`${sel}: ${el.tagName}.${(el.className||'').substring(0,30)}`);
                        }
                    }
                }
                return clicked;
            }
        """)
        if expand_results:
            print(f"  🔍 可展开元素: {expand_results}")
    except Exception:
        pass

    # 也滚动 iframe 内容（飞书智能纪要等文档的正文在 iframe 中）
    for frame in page.frames:
        if frame == page.main_frame:
            continue
        try:
            frame.evaluate("""
                async () => {
                    const delay = ms => new Promise(r => setTimeout(r, ms));
                    const body = document.body || document.documentElement;
                    if (body.scrollHeight <= body.clientHeight + 100) return;
                    let prevHeight = 0;
                    let stableCount = 0;
                    for (let round = 0; round < 10; round++) {
                        let pos = 0;
                        const step = Math.max(window.innerHeight || 600, 300);
                        while (pos < body.scrollHeight) {
                            window.scrollTo(0, pos);
                            await delay(200);
                            pos += step;
                        }
                        window.scrollTo(0, body.scrollHeight);
                        await delay(400);
                        if (body.scrollHeight === prevHeight) {
                            stableCount++;
                            if (stableCount >= 2) break;
                        } else { stableCount = 0; }
                        prevHeight = body.scrollHeight;
                    }
                    window.scrollTo(0, 0);
                }
            """)
        except Exception:
            pass
    time.sleep(1)

    # 获取标题
    title = get_doc_title(page)
    doc_name = title if title else doc_token
    print(f"  📄 标题: {doc_name}")
    markdown = extract_markdown_from_runtime_model(page)
    if markdown and len(markdown) > 100:
        print(f"  ✅ 已使用飞书运行时块模型提取正文（长度 {len(markdown)}）")
    else:
        print("  ⚠️  运行时块模型提取不足，回退到 DOM 提取")
        html = extract_content_html(page)
        if not html or len(html) < 50:
            print(f"  ❌ 未能提取到文档内容")
            return False

        # HTML → Markdown
        markdown = md(html, heading_style="ATX", bullets="-", strip=["script", "style"])

        # 清理：修复列表项（把分离的 bullet 和内容合并）
        markdown = re.sub(r'([•\-\*])\s*\n\n\s*', r'- ', markdown)

        # 清理：修复有序列表（把分离的序号和内容合并）
        markdown = re.sub(r'(\d+\.)\s*\n\n\s*', r'\1 ', markdown)

        markdown = cleanup_markdown(markdown)

        # DOM 回退时仍补标题，避免内容上下文太弱
        if title:
            first_line = markdown.strip().split('\n')[0] if markdown.strip() else ""
            if title not in first_line:
                markdown = f"# {title}\n\n{markdown}"

    # 创建输出目录并保存
    doc_dir = OUTPUT_DIR / doc_name
    doc_dir.mkdir(parents=True, exist_ok=True)

    # 下载图片（带 cookies 认证）
    markdown = download_images(markdown, doc_dir, page)

    # 保存 Markdown
    md_path = doc_dir / f"{doc_name}.md"
    md_path.write_text(markdown, encoding="utf-8")
    print(f"  ✅ 已保存: {md_path.relative_to(SKILL_DIR)}")
    return True


def main():
    global OUTPUT_DIR, PROGRESS_FILE

    # 解析 --output 和 --progress 参数
    args = sys.argv[1:]
    positional = []
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            OUTPUT_DIR = Path(args[i + 1])
            i += 2
        elif args[i].startswith("--output="):
            OUTPUT_DIR = Path(args[i].split("=", 1)[1])
            i += 1
        else:
            positional.append(args[i])
            i += 1

    # 读取链接：支持传单个 URL，或传链接文件
    arg = positional[0] if positional else ""
    if arg.startswith("http://") or arg.startswith("https://"):
        links = [arg]
    else:
        if arg:
            links_file = Path(arg)
        elif DEFAULT_LINKS_FILE.exists():
            links_file = DEFAULT_LINKS_FILE
        else:
            links_file = LEGACY_LINKS_FILE

        if not links_file.exists():
            print(f"❌ 未找到链接输入。可传单个 URL，或在脚本目录放 links.txt")
            sys.exit(1)

        links = read_links(links_file)

    if not links:
        print("❌ 没有读到任何有效链接")
        sys.exit(1)

    print(f"📋 共 {len(links)} 个链接")

    # 加载进度
    completed = load_progress()
    remaining = [url for url in links if url not in completed]
    if completed:
        print(f"⏭️  跳过已完成的 {len(completed)} 个，剩余 {len(remaining)} 个")

    if not remaining:
        print("🎉 所有链接已处理完成！")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser, context = ensure_login(pw, remaining[0])
        page = context.new_page()

        for i, url in enumerate(remaining, 1):
            print(f"\n[{i}/{len(remaining)}] {url}")

            success = False
            for attempt in range(MAX_RETRIES + 1):
                if attempt > 0:
                    print(f"  🔄 重试 ({attempt}/{MAX_RETRIES})")
                    time.sleep(2)
                try:
                    success = export_single_doc(page, url)
                    if success:
                        break
                except Exception as e:
                    print(f"  ❌ 异常: {e}")

            if success:
                completed.add(url)
                save_progress(completed)

            # 延迟
            if i < len(remaining):
                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                time.sleep(delay)

        page.close()
        browser.close()  # 断开 CDP 连接（debug Chrome 继续运行，保留登录态）

    # 统计
    failed = len(remaining) - len([u for u in remaining if u in completed])
    print(f"\n{'=' * 50}")
    print(f"✅ 成功: {len(completed)}/{len(links)}")
    if failed:
        print(f"❌ 失败: {failed}")
    print(f"📁 输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
