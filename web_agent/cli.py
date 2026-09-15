# -*- coding: utf-8 -*-
"""命令行入口。

示例：
  # 采集公告列表的指定字段，导出 CSV
  python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices \
      --fields 标题,发布时间,链接 --format csv --out notices.csv

  # 多网页采集并按编号去重，导出 Excel（可选功能）
  python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices \
      --pages all --dedup-by 编号 --format xlsx --out notices.xlsx

  # 采集详情页（单条记录）
  python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices/N-01 \
      --kind item --fields 标题,发布单位,发布时间,正文

  # 自然语言端到端
  python -m web_agent.cli agent --base http://127.0.0.1:5099 \
      --text "把前两页公告的标题、发布时间和链接导出成 Excel"
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from .agent import WebAgent
from .extract import collect


def _fields(raw):
    if not raw:
        return None
    return [f.strip() for f in raw.replace("，", ",").split(",") if f.strip()]


def _pages(raw):
    if not raw:
        return [1]
    if raw.strip().lower() == "all":
        return "all"
    out = []
    for token in raw.replace("，", ",").split(","):
        token = token.strip()
        if token.isdigit():
            out.append(int(token))
    return out or [1]


def cmd_collect(args) -> dict:
    fields = _fields(args.fields)
    pages = _pages(args.pages)

    if args.kind == "item":
        res = collect(args.base, args.path, kind="item", fields=fields, headless=not args.headed)
        collected = {"records": res["records"], "count": res["count"],
                     "missing_fields": res["missing_fields"], "duplicates_removed": 0}
    elif pages == "all" or len(pages) > 1:
        agent = WebAgent(args.base, headless=not args.headed)
        collected = agent.collect_pages(args.path, pages, fields, args.dedup_by)
    else:
        res = collect(args.base, args.path, kind=args.kind, row_selector=args.row_selector,
                      fields=fields, headless=not args.headed)
        collected = {"records": res["records"], "count": res["count"],
                     "missing_fields": res["missing_fields"], "duplicates_removed": 0}

    records = collected["records"]
    agent = WebAgent(args.base, headless=not args.headed)
    exported = agent.export_result(records, args.format, args.out)

    return {
        "ok": True,
        "action": "collect",
        "count": collected["count"],
        "duplicates_removed": collected.get("duplicates_removed", 0),
        "missing_fields": collected.get("missing_fields", []),
        "records": records,
        "export": exported,
    }


def cmd_agent(args) -> dict:
    agent = WebAgent(args.base, headless=not args.headed)
    return agent.run(args.text, out=args.out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="web_agent", description="AI 网页信息采集智能体")
    parser.add_argument("--verbose", action="store_true", help="输出调试日志")
    sub = parser.add_subparsers(dest="command", required=True)

    pc = sub.add_parser("collect", help="采集指定网页的字段并导出")
    pc.add_argument("--base", default="http://127.0.0.1:5099", help="目标站点根地址")
    pc.add_argument("--path", default="/notices", help="目标路径或完整 URL")
    pc.add_argument("--fields", default="", help="要采集的字段，逗号分隔；留空表示采集全部列")
    pc.add_argument("--format", default="json", choices=["json", "csv", "xlsx"], help="导出格式")
    pc.add_argument("--out", default=None, help="输出文件路径；省略时自动写入 exports/ 目录")
    pc.add_argument("--kind", default="auto", choices=["auto", "table", "list", "item"], help="目标页面结构")
    pc.add_argument("--row-selector", default=None, help="自定义行/卡片选择器（kind=table 或 list 时生效）")
    pc.add_argument("--pages", default="", help="页码，如 1,2 或 all（多页采集）")
    pc.add_argument("--dedup-by", default=None, help="多页采集时的去重字段")
    pc.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    pc.set_defaults(func=cmd_collect)

    pa = sub.add_parser("agent", help="自然语言端到端采集")
    pa.add_argument("--base", default="http://127.0.0.1:5099", help="目标站点根地址")
    pa.add_argument("--text", required=True, help="自然语言需求")
    pa.add_argument("--out", default=None, help="输出文件路径")
    pa.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    pa.set_defaults(func=cmd_agent)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s")
    try:
        result = args.func(args)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())