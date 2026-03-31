#!/usr/bin/env python3
"""飞书云空间知识库 — 内容矩阵素材管理后端

用法:
  python feishu_drive.py init <项目名>
  python feishu_drive.py write <项目名> <路径> <md文件|->
  python feishu_drive.py list <项目名> [路径]
  python feishu_drive.py search <项目名> <关键词>
  python feishu_drive.py read <项目名> <文档token>
  python feishu_drive.py update <项目名> <文档token> <md文件|->
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

CONFIG_PATH = os.path.expanduser("~/.content-organizer/config.json")

# .env 文件搜索路径（从脚本位置向上找）
def _find_dotenv():
    """向上查找 .env 文件"""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        env_path = os.path.join(d, ".env")
        if os.path.exists(env_path):
            return env_path
        d = os.path.dirname(d)
    return None


def _load_dotenv():
    """简易 .env 加载器，将变量注入 os.environ（不覆盖已有值）"""
    path = _find_dotenv()
    if not path:
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if not os.environ.get(key):
                os.environ[key] = value


_load_dotenv()

# 素材库目录结构
FOLDER_TREE = {
    "素材库": {
        "1-客户案例": {},
        "2-交付故事": {},
        "3-行业知识": {},
        "4-爆款参考": {
            "小红书": {},
            "抖音": {},
        },
        "5-选题报告": {},
        "6-内容产出": {
            "小红书": {},
            "抖音": {},
            "公众号": {},
            "视频号": {},
        },
        "7-发布日志": {},
        "8-长尾关键词库": {},
        "9-客户画像": {},
    }
}


# ── API helpers ──────────────────────────────────────────────

def load_config():
    """加载配置，.env 环境变量优先，config.json 兜底"""
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
    # 环境变量覆盖 config.json 中的凭证
    cfg["app_id"] = os.environ.get("FEISHU_APP_ID", cfg.get("app_id", ""))
    cfg["app_secret"] = os.environ.get("FEISHU_APP_SECRET", cfg.get("app_secret", ""))
    cfg.setdefault("root_folder_token", "")
    cfg.setdefault("projects", {})
    if not cfg["app_id"] or not cfg["app_secret"]:
        print("错误: 未找到飞书凭证。请在 .env 中设置 FEISHU_APP_ID / FEISHU_APP_SECRET，"
              f"或在 {CONFIG_PATH} 中配置。", file=sys.stderr)
        sys.exit(1)
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_token(cfg):
    """获取 tenant_access_token"""
    data = json.dumps({
        "app_id": cfg["app_id"],
        "app_secret": cfg["app_secret"],
    }).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    if body.get("code") != 0:
        print(f"获取 token 失败: {body}", file=sys.stderr)
        sys.exit(1)
    return body["tenant_access_token"]


def api(method, path, token, body=None, params=None):
    """通用飞书 API 调用"""
    url = f"https://open.feishu.cn/open-apis{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"API 错误 [{e.code}]: {err_body}", file=sys.stderr)
        sys.exit(1)


# ── 文件夹操作 ───────────────────────────────────────────────

def create_folder(token, parent_token, name):
    """创建文件夹，返回 folder_token"""
    resp = api("POST", "/drive/v1/files/create_folder", token, {
        "name": name,
        "folder_token": parent_token,
    })
    return resp["data"]["token"]


def list_folder(token, folder_token, page_size=50):
    """列出文件夹内容，自动分页"""
    items = []
    page_token = None
    while True:
        params = {"folder_token": folder_token, "page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        resp = api("GET", "/drive/v1/files", token, params=params)
        data = resp.get("data", {})
        items.extend(data.get("files", []))
        if not data.get("has_more"):
            break
        page_token = data.get("next_page_token")
    return items


def find_child(token, parent_token, name):
    """在文件夹中按名称查找子项，返回 token 或 None"""
    for item in list_folder(token, parent_token):
        if item.get("name") == name:
            return item.get("token"), item.get("type")
    return None, None


def ensure_folder_path(token, root_token, path_parts):
    """确保路径存在，不存在则创建，返回最终 folder_token"""
    current = root_token
    for part in path_parts:
        child_token, child_type = find_child(token, current, part)
        if child_token and child_type == "folder":
            current = child_token
        else:
            current = create_folder(token, current, part)
    return current


# ── DocX 操作 ────────────────────────────────────────────────

def create_docx(token, folder_token, title):
    """创建 DocX 文档，返回 document_id"""
    resp = api("POST", "/docx/v1/documents", token, {
        "title": title,
        "folder_token": folder_token,
    })
    return resp["data"]["document"]["document_id"]


def write_blocks(token, doc_id, blocks):
    """向文档追加 blocks（每批最多 50 个）"""
    for i in range(0, len(blocks), 50):
        batch = blocks[i:i + 50]
        api("POST", f"/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
            token, {"children": batch})


def get_doc_blocks(token, doc_id):
    """读取文档所有 blocks"""
    items = []
    page_token = None
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        resp = api("GET", f"/docx/v1/documents/{doc_id}/blocks", token, params=params)
        data = resp.get("data", {})
        items.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    return items


def delete_doc_children(token, doc_id):
    """删除文档内所有子 block（用于 update 前清空）"""
    blocks = get_doc_blocks(token, doc_id)
    child_ids = [b["block_id"] for b in blocks if b.get("parent_id") == doc_id]
    if not child_ids:
        return
    # 批量删除
    for i in range(0, len(child_ids), 30):
        batch = child_ids[i:i + 30]
        api("DELETE", f"/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete",
            token, {"children": batch})


# ── Markdown → Blocks 转换 ──────────────────────────────────

def parse_inline(text):
    """解析行内格式（粗体、斜体、行内代码），返回 elements 列表"""
    elements = []
    # 用正则拆分 **bold**, *italic*, `code`
    pattern = r'(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)'
    last_end = 0
    for m in re.finditer(pattern, text):
        # 前面的普通文本
        if m.start() > last_end:
            plain = text[last_end:m.start()]
            if plain:
                elements.append({"text_run": {"content": plain}})
        if m.group(2):  # **bold**
            elements.append({"text_run": {
                "content": m.group(2),
                "text_element_style": {"bold": True},
            }})
        elif m.group(3):  # *italic*
            elements.append({"text_run": {
                "content": m.group(3),
                "text_element_style": {"italic": True},
            }})
        elif m.group(4):  # `code`
            elements.append({"text_run": {
                "content": m.group(4),
                "text_element_style": {"inline_code": True},
            }})
        last_end = m.end()
    # 尾部文本
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            elements.append({"text_run": {"content": remaining}})
    if not elements:
        elements.append({"text_run": {"content": text}})
    return elements


def _text_block(block_type, text, key=None):
    """构造文本类 block"""
    if key is None:
        key_map = {2: "text", 3: "heading1", 4: "heading2", 5: "heading3",
                   6: "heading4", 7: "heading5", 8: "heading6",
                   12: "bullet", 13: "ordered", 15: "quote"}
        key = key_map.get(block_type, "text")
    block_body = {"elements": parse_inline(text)}
    # 列表类 block 不能传空 style，其余可以
    if block_type not in (12, 13, 17):
        block_body["style"] = {}
    return {"block_type": block_type, key: block_body}


def md_to_blocks(md_text):
    """将 Markdown 文本转为飞书 DocX blocks 列表"""
    blocks = []
    lines = md_text.split("\n")
    i = 0

    # 处理 frontmatter
    if lines and lines[0].strip() == "---":
        fm_lines = ["---"]
        i = 1
        while i < len(lines):
            fm_lines.append(lines[i])
            if lines[i].strip() == "---":
                i += 1
                break
            i += 1
        # frontmatter 存为代码块
        blocks.append({
            "block_type": 14,
            "code": {
                "elements": [{"text_run": {"content": "\n".join(fm_lines)}}],
                "style": {"language": 25},  # 25 = YAML
            },
        })

    # 处理正文
    in_code_block = False
    code_lines = []
    code_lang = 0

    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                lang_hint = line.strip()[3:].strip().lower()
                lang_map = {"python": 18, "javascript": 12, "json": 14,
                            "bash": 3, "shell": 3, "markdown": 16,
                            "yaml": 25, "html": 10, "css": 6}
                code_lang = lang_map.get(lang_hint, 1)  # 1=PlainText, 0 is invalid
                code_lines = []
            else:
                in_code_block = False
                blocks.append({
                    "block_type": 14,
                    "code": {
                        "elements": [{"text_run": {"content": "\n".join(code_lines)}}],
                        "style": {"language": code_lang},
                    },
                })
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # 空行跳过
        if not stripped:
            i += 1
            continue

        # 分割线
        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped):
            blocks.append({"block_type": 22, "divider": {}})
            i += 1
            continue

        # 标题
        heading_match = re.match(r'^(#{1,6})\s+(.+)', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            block_type = 2 + level  # H1=3, H2=4, ...
            blocks.append(_text_block(block_type, text))
            i += 1
            continue

        # 无序列表 (block_type 12 = bullet)
        if re.match(r'^[-*+]\s+', stripped):
            text = re.sub(r'^[-*+]\s+', '', stripped)
            blocks.append(_text_block(12, text))
            i += 1
            continue

        # 有序列表 (block_type 13 = ordered)
        ol_match = re.match(r'^\d+\.\s+(.+)', stripped)
        if ol_match:
            blocks.append(_text_block(13, ol_match.group(1)))
            i += 1
            continue

        # 引用
        if stripped.startswith(">"):
            text = stripped[1:].strip()
            blocks.append(_text_block(15, text))
            i += 1
            continue

        # 表格 → 降级为代码块
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            blocks.append({
                "block_type": 14,
                "code": {
                    "elements": [{"text_run": {"content": "\n".join(table_lines)}}],
                    "style": {"language": 16},  # 16=Markdown
                },
            })
            continue

        # 普通文本
        blocks.append(_text_block(2, stripped))
        i += 1

    return blocks


# ── Blocks → Markdown 转换 ──────────────────────────────────

def _extract_text(elements):
    """从 elements 列表提取纯文本"""
    parts = []
    for el in (elements or []):
        tr = el.get("text_run", {})
        content = tr.get("content", "")
        style = tr.get("text_element_style", {})
        if style.get("bold"):
            content = f"**{content}**"
        if style.get("italic"):
            content = f"*{content}*"
        if style.get("inline_code"):
            content = f"`{content}`"
        parts.append(content)
    return "".join(parts)


def blocks_to_md(blocks):
    """将飞书 DocX blocks 转回 Markdown"""
    lines = []
    for block in blocks:
        bt = block.get("block_type")
        if bt == 1:  # page (skip title, already in doc title)
            continue
        elif bt == 2:  # text
            text = _extract_text(block.get("text", {}).get("elements"))
            lines.append(text)
        elif bt in (3, 4, 5, 6, 7, 8):  # heading 1-6
            key_map = {3: "heading1", 4: "heading2", 5: "heading3",
                       6: "heading4", 7: "heading5", 8: "heading6"}
            level = bt - 2
            data = block.get(key_map[bt], {})
            text = _extract_text(data.get("elements"))
            lines.append(f"{'#' * level} {text}")
        elif bt == 12:  # bullet (unordered list)
            text = _extract_text(block.get("bullet", {}).get("elements"))
            lines.append(f"- {text}")
        elif bt == 13:  # ordered list
            text = _extract_text(block.get("ordered", {}).get("elements"))
            lines.append(f"1. {text}")
        elif bt == 14:  # code
            code_data = block.get("code", {})
            text = _extract_text(code_data.get("elements"))
            lines.append(f"```\n{text}\n```")
        elif bt == 15:  # quote
            text = _extract_text(block.get("quote", {}).get("elements"))
            lines.append(f"> {text}")
        elif bt == 22:  # divider
            lines.append("---")
        lines.append("")  # blank line between blocks
    return "\n".join(lines)


# ── 命令实现 ─────────────────────────────────────────────────

def cmd_init(args):
    """初始化项目文件夹结构"""
    cfg = load_config()
    token = get_token(cfg)
    project = args.project

    # 自动获取 root_folder_token（首次运行时）
    root = cfg.get("root_folder_token")
    if not root:
        resp = api("GET", "/drive/explorer/v2/root_folder/meta", token)
        root = resp["data"]["token"]
        cfg["root_folder_token"] = root
        save_config(cfg)

    if project in cfg.get("projects", {}):
        print(f"项目 '{project}' 已存在，folder_token: {cfg['projects'][project]['folder_token']}")
        return

    print(f"正在创建项目 '{project}' ...")
    project_folder = create_folder(token, root, project)

    def _build_tree(parent_token, tree, depth=0):
        for name, children in tree.items():
            indent = "  " * depth
            print(f"{indent}  创建: {name}/")
            folder = create_folder(token, parent_token, name)
            if children:
                _build_tree(folder, children, depth + 1)

    _build_tree(project_folder, FOLDER_TREE)

    cfg.setdefault("projects", {})[project] = {
        "folder_token": project_folder,
        "created_at": time.strftime("%Y-%m-%d"),
    }
    save_config(cfg)
    print(f"\n✅ 项目 '{project}' 创建完成")
    print(f"   飞书链接: https://gcn6bvkburhk.feishu.cn/drive/folder/{project_folder}")


def cmd_write(args):
    """写入一篇 Markdown 笔记到飞书"""
    cfg = load_config()
    token = get_token(cfg)
    project = args.project
    proj = cfg.get("projects", {}).get(project)
    if not proj:
        print(f"错误: 项目 '{project}' 不存在，请先运行 init", file=sys.stderr)
        sys.exit(1)

    # 读取 md 内容
    if args.md_file == "-":
        md_text = sys.stdin.read()
    else:
        with open(args.md_file) as f:
            md_text = f.read()

    # 解析路径（如 "1-客户案例/张姐-深度保洁"）
    path_parts = args.path.strip("/").split("/")
    doc_title = path_parts[-1]
    folder_parts = ["素材库"] + path_parts[:-1]

    # 确保文件夹存在
    target_folder = ensure_folder_path(token, proj["folder_token"], folder_parts)

    # 创建文档
    doc_id = create_docx(token, target_folder, doc_title)
    print(f"文档已创建: {doc_title} (id: {doc_id})")

    # 转换并写入内容
    blocks = md_to_blocks(md_text)
    if blocks:
        write_blocks(token, doc_id, blocks)
        print(f"✅ 已写入 {len(blocks)} 个内容块")
    else:
        print("⚠️ Markdown 内容为空，文档已创建但无正文")

    print(f"   飞书链接: https://gcn6bvkburhk.feishu.cn/docx/{doc_id}")


def cmd_list(args):
    """列出项目目录内容"""
    cfg = load_config()
    token = get_token(cfg)
    project = args.project
    proj = cfg.get("projects", {}).get(project)
    if not proj:
        print(f"错误: 项目 '{project}' 不存在", file=sys.stderr)
        sys.exit(1)

    # 导航到目标路径
    current = proj["folder_token"]
    if args.path:
        path_parts = ["素材库"] + args.path.strip("/").split("/")
    else:
        path_parts = ["素材库"]

    for part in path_parts:
        child_token, child_type = find_child(token, current, part)
        if not child_token:
            print(f"错误: 路径 '{part}' 不存在", file=sys.stderr)
            sys.exit(1)
        current = child_token

    # 列出内容
    items = list_folder(token, current)
    if not items:
        print("(空)")
        return

    for item in items:
        type_icon = "📁" if item.get("type") == "folder" else "📄"
        name = item.get("name", "未命名")
        token_val = item.get("token", "")
        print(f"  {type_icon} {name}  [{token_val}]")

    print(f"\n共 {len(items)} 项")


def cmd_search(args):
    """在项目中搜索笔记"""
    cfg = load_config()
    token = get_token(cfg)
    project = args.project
    proj = cfg.get("projects", {}).get(project)
    if not proj:
        print(f"错误: 项目 '{project}' 不存在", file=sys.stderr)
        sys.exit(1)

    keyword = args.keyword

    # 用飞书搜索 API
    resp = api("POST", "/suite/docs-api/search/object", token, {
        "search_key": keyword,
        "count": 20,
        "offset": 0,
        "owner_ids": [],
        "docs_types": [22],  # 22 = docx
    })

    results = resp.get("data", {}).get("docs_entities", [])
    if not results:
        print(f"未找到与 '{keyword}' 相关的文档")
        return

    print(f"搜索 '{keyword}' 结果:\n")
    for doc in results:
        title = doc.get("title", "未命名")
        doc_token = doc.get("docs_token", "")
        url = doc.get("url", "")
        print(f"  📄 {title}")
        print(f"     token: {doc_token}")
        if url:
            print(f"     链接: {url}")
        print()

    print(f"共 {len(results)} 条结果")


def cmd_read(args):
    """读取文档内容并转回 Markdown"""
    cfg = load_config()
    token = get_token(cfg)

    doc_id = args.doc_token
    blocks = get_doc_blocks(token, doc_id)
    md = blocks_to_md(blocks)
    print(md)


def cmd_update(args):
    """更新已有文档内容"""
    cfg = load_config()
    token = get_token(cfg)

    doc_id = args.doc_token

    # 读取新内容
    if args.md_file == "-":
        md_text = sys.stdin.read()
    else:
        with open(args.md_file) as f:
            md_text = f.read()

    # 清空原有内容
    delete_doc_children(token, doc_id)

    # 写入新内容
    blocks = md_to_blocks(md_text)
    if blocks:
        write_blocks(token, doc_id, blocks)
        print(f"✅ 文档 {doc_id} 已更新，写入 {len(blocks)} 个内容块")
    else:
        print("⚠️ 新内容为空")


# ── CLI 入口 ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="飞书云空间知识库管理")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="初始化项目文件夹结构")
    p_init.add_argument("project", help="项目名称")

    p_write = sub.add_parser("write", help="写入 Markdown 笔记")
    p_write.add_argument("project", help="项目名称")
    p_write.add_argument("path", help="目标路径（如 1-客户案例/张姐-深度保洁）")
    p_write.add_argument("md_file", help="Markdown 文件路径，用 - 表示 stdin")

    p_list = sub.add_parser("list", help="列出目录内容")
    p_list.add_argument("project", help="项目名称")
    p_list.add_argument("path", nargs="?", default=None, help="子路径")

    p_search = sub.add_parser("search", help="搜索笔记")
    p_search.add_argument("project", help="项目名称")
    p_search.add_argument("keyword", help="搜索关键词")

    p_read = sub.add_parser("read", help="读取文档内容")
    p_read.add_argument("project", help="项目名称")
    p_read.add_argument("doc_token", help="文档 token / document_id")

    p_update = sub.add_parser("update", help="更新文档内容")
    p_update.add_argument("project", help="项目名称")
    p_update.add_argument("doc_token", help="文档 token / document_id")
    p_update.add_argument("md_file", help="Markdown 文件路径，用 - 表示 stdin")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "init": cmd_init,
        "write": cmd_write,
        "list": cmd_list,
        "search": cmd_search,
        "read": cmd_read,
        "update": cmd_update,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
