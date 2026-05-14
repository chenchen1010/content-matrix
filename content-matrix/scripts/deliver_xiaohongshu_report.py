#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_TOPIC_FIELDS = [
    {"field_name": "选题", "type": 1},
    {"field_name": "阶段", "type": 3, "property": {"options": [
        {"name": "A1"}, {"name": "A2"}, {"name": "A3"}, {"name": "A4"}, {"name": "A5"}
    ]}},
    {"field_name": "核心问题", "type": 1},
    {"field_name": "推荐打法", "type": 1},
    {"field_name": "推荐账号类型", "type": 1},
    {"field_name": "内容形式", "type": 1},
    {"field_name": "互动信号", "type": 1},
    {"field_name": "是否已验证", "type": 3, "property": {"options": [
        {"name": "已验证"}, {"name": "待验证"}
    ]}},
    {"field_name": "参考案例", "type": 1},
    {"field_name": "优先级", "type": 3, "property": {"options": [
        {"name": "高"}, {"name": "中"}, {"name": "低"}
    ]}},
    {"field_name": "备注", "type": 1},
]


def run_json(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}")
    text = result.stdout.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from command: {' '.join(cmd)}\nOutput:\n{text}") from e


def lark_api(method, path, data=None, params=None, as_user=True):
    cmd = ["lark-cli", "api", method, path]
    if as_user:
        cmd += ["--as", "user"]
    if params is not None:
        cmd += ["--params", json.dumps(params, ensure_ascii=False)]
    if data is not None:
        cmd += ["--data", json.dumps(data, ensure_ascii=False)]
    return run_json(cmd)



def lark_docs_create(title, markdown, wiki_space=None, wiki_node=None, folder_token=None):
    cmd = ["lark-cli", "docs", "+create", "--as", "user", "--title", title, "--markdown", markdown]
    if wiki_space:
        cmd += ["--wiki-space", wiki_space]
    if wiki_node:
        cmd += ["--wiki-node", wiki_node]
    if folder_token:
        cmd += ["--folder-token", folder_token]
    return run_json(cmd)



def send_self_message(text):
    user_info = lark_api("GET", "/open-apis/authen/v1/user_info")
    data = (user_info or {}).get("data") or {}
    open_id = data.get("open_id")
    if not open_id:
        return None
    body = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}, ensure_ascii=False),
    }
    return lark_api("POST", "/open-apis/im/v1/messages", data=body, params={"receive_id_type": "open_id"})



def pick_first(*values):
    for value in values:
        if value:
            return value
    return None



def get_nested(data, *path):
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
        if cur is None:
            return None
    return cur



def normalize_lines(value):
    if not value:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                title = pick_first(item.get("title"), item.get("name"), item.get("label"), item.get("选题"), item.get("heading"))
                desc = pick_first(item.get("description"), item.get("summary"), item.get("value"), item.get("说明"), item.get("reason"))
                if title and desc:
                    out.append(f"- **{title}**：{desc}")
                elif title:
                    out.append(f"- {title}")
                elif desc:
                    out.append(f"- {desc}")
        return out
    return [str(value)]



def ensure_tag_prefix(tags):
    clean = []
    for tag in tags or []:
        tag = str(tag).strip()
        if not tag:
            continue
        clean.append(tag if tag.startswith("#") else f"#{tag}")
    return clean



def extract_doc_token(resp):
    candidates = [
        get_nested(resp, "data", "document", "document_id"),
        get_nested(resp, "data", "document_id"),
        get_nested(resp, "data", "doc_id"),
        get_nested(resp, "document", "document_id"),
        get_nested(resp, "data", "token"),
        get_nested(resp, "token"),
    ]
    for candidate in candidates:
        if candidate:
            return candidate
    return None



def extract_doc_url(resp, token):
    candidates = [
        get_nested(resp, "data", "url"),
        get_nested(resp, "data", "doc_url"),
        get_nested(resp, "data", "document", "url"),
        get_nested(resp, "url"),
    ]
    for candidate in candidates:
        if candidate:
            return candidate
    if token:
        return f"https://feishu.cn/docx/{token}"
    return None



def extract_bitable_tokens(resp):
    data = (resp or {}).get("data") or {}
    app = data.get("app") or data.get("item") or data
    app_token = app.get("app_token") or app.get("token") or data.get("app_token")
    url = app.get("url") or data.get("url")
    return app_token, url



def extract_table_id(resp):
    data = (resp or {}).get("data") or {}
    table = data.get("table") or data.get("item") or data
    return table.get("table_id") or table.get("id") or data.get("table_id")



def create_bitable(payload):
    business_name = pick_first(payload.get("business_name"), payload.get("project_name"), payload.get("industry"), "小红书选题调研")
    folder_token = payload.get("feishu_folder_token") or os.environ.get("FEISHU_FOLDER_TOKEN") or ""
    create_app_resp = lark_api(
        "POST",
        "/open-apis/bitable/v1/apps",
        data={"name": f"{business_name} - 小红书选题库", "folder_token": folder_token},
    )
    app_token, app_url = extract_bitable_tokens(create_app_resp)
    if not app_token:
        raise RuntimeError(f"Unable to extract app_token from response: {json.dumps(create_app_resp, ensure_ascii=False, indent=2)}")

    table_resp = lark_api(
        "POST",
        f"/open-apis/bitable/v1/apps/{app_token}/tables",
        data={
            "table": {
                "name": "选题库",
                "default_view_name": "全部选题",
                "fields": DEFAULT_TOPIC_FIELDS,
            }
        },
    )
    table_id = extract_table_id(table_resp)
    if not table_id:
        raise RuntimeError(f"Unable to extract table_id from response: {json.dumps(table_resp, ensure_ascii=False, indent=2)}")

    rows = payload.get("topic_rows") or []
    for row in rows:
        fields = {
            "选题": row.get("选题") or row.get("topic") or row.get("title") or "",
            "阶段": row.get("阶段") or row.get("stage") or row.get("a_layer") or "A2",
            "核心问题": row.get("核心问题") or row.get("problem") or row.get("pain_point") or "",
            "推荐打法": row.get("推荐打法") or row.get("playbook") or row.get("approach") or "",
            "推荐账号类型": row.get("推荐账号类型") or row.get("account_type") or "",
            "内容形式": row.get("内容形式") or row.get("content_format") or row.get("format") or "",
            "互动信号": row.get("互动信号") or row.get("engagement_signal") or row.get("signal") or "",
            "是否已验证": row.get("是否已验证") or row.get("validated") or "待验证",
            "参考案例": row.get("参考案例") or row.get("reference") or row.get("example") or "",
            "优先级": row.get("优先级") or row.get("priority") or "中",
            "备注": row.get("备注") or row.get("notes") or row.get("reason") or "",
        }
        lark_api(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
            data={"fields": fields},
        )

    if not app_url:
        app_url = f"https://feishu.cn/base/{app_token}"
    return {"app_token": app_token, "table_id": table_id, "url": app_url}



def build_markdown(payload, bitable_url):
    title = pick_first(payload.get("title"), payload.get("doc_title"), payload.get("business_name"), payload.get("project_name"), "小红书选题调研")
    city = payload.get("city") or payload.get("region") or ""
    industry = payload.get("industry") or ""
    identity = payload.get("business_identity") or payload.get("identity") or ""
    audience = payload.get("target_audience") or payload.get("audience") or ""
    summary = payload.get("business_summary") or payload.get("summary") or ""
    keywords = payload.get("seed_keywords") or payload.get("keywords") or []

    report = payload.get("report") or {}
    notes = payload.get("demo_notes") or []
    topic_rows = payload.get("topic_rows") or []

    sections = [
        ("调研摘要", pick_first(report.get("executive_summary"), payload.get("executive_summary"))),
        ("行业现状", pick_first(report.get("industry_overview"), report.get("market_overview"), payload.get("industry_overview"))),
        ("玩家格局", pick_first(report.get("player_landscape"), report.get("player_map"), payload.get("player_landscape"))),
        ("内容供给观察", pick_first(report.get("content_supply"), report.get("content_patterns"), payload.get("content_supply"))),
        ("用户需求与搜索意图", pick_first(report.get("user_needs"), report.get("search_intent"), payload.get("user_needs"))),
        ("阶段画像", pick_first(report.get("stage_personas"), report.get("personas"), payload.get("stage_personas"))),
        ("有效打法分析", pick_first(report.get("effective_playbooks"), report.get("playbook_insights"), payload.get("effective_playbooks"))),
        ("机会缺口", pick_first(report.get("opportunity_gaps"), report.get("opportunities"), payload.get("opportunity_gaps"))),
        ("选题策略", pick_first(report.get("topic_strategy"), report.get("topic_recommendations"), payload.get("topic_strategy"))),
        ("建议发布顺序", pick_first(report.get("action_plan"), report.get("next_actions"), payload.get("action_plan"))),
    ]

    lines = [f"# {title}", "", "## 业务背景", ""]
    if summary:
        lines.append(summary)
        lines.append("")
    if city:
        lines.append(f"- 城市/区域：{city}")
    if industry:
        lines.append(f"- 行业：{industry}")
    if identity:
        lines.append(f"- 业务身份：{identity}")
    if audience:
        lines.append(f"- 目标客户：{audience}")
    if keywords:
        lines.append(f"- 种子关键词：{', '.join(str(k) for k in keywords)}")
    lines.append(f"- 选题库条数：{len(topic_rows)}")
    lines.append(f"- 示范笔记条数：{len(notes)}")

    def add_section(name, items):
        items = normalize_lines(items)
        if not items:
            return
        lines.extend(["", f"## {name}", ""])
        for item in items:
            if item.startswith("- "):
                lines.append(item)
            else:
                lines.append(f"- {item}")

    for section_name, section_value in sections:
        add_section(section_name, section_value)

    if topic_rows:
        lines.extend(["", "## 高优先级选题预览", ""])
        preview_rows = topic_rows[:10]
        for idx, row in enumerate(preview_rows, 1):
            topic = row.get("选题") or row.get("topic") or row.get("title") or f"选题 {idx}"
            stage = row.get("阶段") or row.get("stage") or row.get("a_layer") or "A2"
            problem = row.get("核心问题") or row.get("problem") or row.get("pain_point") or ""
            playbook = row.get("推荐打法") or row.get("playbook") or row.get("approach") or ""
            lines.append(f"### {idx}. {topic}")
            lines.append(f"- 阶段：{stage}")
            if problem:
                lines.append(f"- 核心问题：{problem}")
            if playbook:
                lines.append(f"- 推荐打法：{playbook}")
            lines.append("")
        if len(topic_rows) > len(preview_rows):
            lines.append(f"其余 {len(topic_rows) - len(preview_rows)} 条选题见下方多维表格。")

    lines.extend([
        "",
        "## 选题库（多维表格）",
        "",
        "下方链接为本次调研的执行选题库。若飞书自动预览生效，会在文档里直接显示；如未自动预览，可点击打开。",
        "",
        bitable_url,
    ])

    lines.extend(["", "## 3 条示范笔记", ""])
    for idx, note in enumerate(notes, 1):
        note_title = note.get("title") or note.get("标题") or f"示范笔记 {idx}"
        note_body = note.get("body") or note.get("正文") or ""
        note_tags = ensure_tag_prefix(note.get("tags") or note.get("标签") or [])
        note_angle = note.get("angle") or note.get("选题角度") or ""
        note_stage = note.get("stage") or note.get("A层") or note.get("阶段") or ""

        lines.extend(["", f"### {idx}. {note_title}", ""])
        meta = []
        if note_stage:
            meta.append(f"阶段：{note_stage}")
        if note_angle:
            meta.append(f"角度：{note_angle}")
        if meta:
            lines.append("- " + " | ".join(meta))
            lines.append("")
        if note_body:
            lines.append(note_body)
            lines.append("")
        if note_tags:
            lines.append("标签：" + " ".join(note_tags))

    lines.extend([
        "",
        "## 使用建议",
        "",
        "- 这不是一锤定音的最终策略，而是第一版作战稿。",
        "- 建议优先从高优先级选题和 3 条示范笔记开始发布。",
        "- 拿到真实反馈后，再围绕互动、咨询和转化继续迭代下一版。",
        "",
    ])
    return "\n".join(lines).strip() + "\n"



def create_doc(payload, markdown):
    title = pick_first(
        payload.get("doc_title"),
        payload.get("title"),
        payload.get("report_title"),
        payload.get("business_name"),
        payload.get("project_name"),
        "小红书选题调研",
    )
    wiki_space = payload.get("wiki_space") or os.environ.get("FEISHU_WIKI_SPACE")
    wiki_node = payload.get("wiki_node") or os.environ.get("FEISHU_WIKI_NODE")
    folder_token = payload.get("feishu_folder_token") or os.environ.get("FEISHU_FOLDER_TOKEN")
    resp = lark_docs_create(title=title, markdown=markdown, wiki_space=wiki_space, wiki_node=wiki_node, folder_token=folder_token)
    token = extract_doc_token(resp)
    url = extract_doc_url(resp, token)
    return {"document_token": token, "url": url, "raw": resp}



def main():
    parser = argparse.ArgumentParser(description="Create a Feishu Xiaohongshu research delivery doc + topic base")
    parser.add_argument("payload", help="Path to JSON payload file")
    parser.add_argument("--notify", action="store_true", help="Send a Feishu message to yourself with the document link")
    args = parser.parse_args()

    payload_path = Path(args.payload)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    bitable = create_bitable(payload)
    markdown = build_markdown(payload, bitable["url"])
    doc = create_doc(payload, markdown)

    message_result = None
    if args.notify and doc.get("url"):
        title = pick_first(payload.get("doc_title"), payload.get("title"), payload.get("business_name"), "小红书选题调研")
        try:
            message_result = send_self_message(f"{title} 已生成：{doc['url']}")
        except Exception as exc:
            message_result = {"ok": False, "error": str(exc)}

    result = {
        "ok": True,
        "doc": {"token": doc.get("document_token"), "url": doc.get("url")},
        "bitable": bitable,
        "message": message_result,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
