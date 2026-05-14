#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

REQUIRED_REPORT_KEYS = [
    "executive_summary",
    "industry_overview",
    "player_landscape",
    "content_supply",
    "user_needs",
    "stage_personas",
    "effective_playbooks",
    "opportunity_gaps",
    "topic_strategy",
    "action_plan",
]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def default_list(v):
    return v if isinstance(v, list) else ([] if v is None else [v])


def merge_payload(base, research=None, notes=None):
    out = dict(base)
    report = dict(out.get("report") or {})

    if research:
        out["doc_title"] = out.get("doc_title") or research.get("doc_title") or research.get("title") or out.get("business_name")
        for key in ["business_name", "city", "industry", "business_identity", "target_audience", "business_summary", "seed_keywords"]:
            if research.get(key) and not out.get(key):
                out[key] = research.get(key)
        research_report = research.get("report") or {}
        for key in REQUIRED_REPORT_KEYS:
            if research_report.get(key):
                report[key] = research_report[key]
        if research.get("topic_rows"):
            out["topic_rows"] = research["topic_rows"]

    if notes and notes.get("demo_notes"):
        out["demo_notes"] = notes["demo_notes"]

    out["report"] = report
    return out


def validate(payload):
    errors = []
    if not payload.get("doc_title"):
        errors.append("missing doc_title")
    if not payload.get("business_name"):
        errors.append("missing business_name")
    if len(default_list(payload.get("seed_keywords"))) < 3:
        errors.append("seed_keywords must contain at least 3 items")
    report = payload.get("report") or {}
    missing_sections = [k for k in REQUIRED_REPORT_KEYS if not default_list(report.get(k))]
    if missing_sections:
        errors.append("missing report sections: " + ", ".join(missing_sections))
    if len(default_list(payload.get("topic_rows"))) < 10:
        errors.append("topic_rows must contain at least 10 items")
    if len(default_list(payload.get("demo_notes"))) < 3:
        errors.append("demo_notes must contain at least 3 items")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Compose and validate Xiaohongshu Feishu delivery payload")
    parser.add_argument("--base", required=True, help="Base payload JSON")
    parser.add_argument("--research", help="Research output JSON")
    parser.add_argument("--notes", help="Demo notes JSON")
    parser.add_argument("--output", required=True, help="Output payload JSON path")
    args = parser.parse_args()

    base = load(args.base)
    research = load(args.research) if args.research else None
    notes = load(args.notes) if args.notes else None
    payload = merge_payload(base, research, notes)
    errors = validate(payload)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "output": str(output_path),
        "topic_rows": len(payload.get("topic_rows") or []),
        "demo_notes": len(payload.get("demo_notes") or []),
        "report_sections": sorted((payload.get("report") or {}).keys())
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
