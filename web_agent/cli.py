# -*- coding: utf-8 -*-
"""命令行入口。

示例：
  # 采集公告列表的指定字段，导出 JSON
  python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices \
      --fields 标题,发布时间,发布单位 --out notices.json

  # 自然语言端到端
  python -m web_agent.cli agent --base http://127.0.0.1:5099 \
      --text "采集公告的标题、发布时间和发布单位"
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from .agent import WebAgent


def _fields(raw):
    if not raw:
        return None
    return [f.strip() for f in raw.replace("，", ",").split(",") if f.strip()]


def cmd_collect(args) -> dict:
    agent = WebAgent(args.base, headless=not args.headed)
    res = agent.collect_page(args.path, fields=_fields(args.fields),
                             row_selector=args.row_selector)
    exported = agent.export_result(res["records"], "json", args.out)
    return {
        "ok": True,
        "action": "collect",
        "count": res["count"],
        "missing_fields": res["missing_fields"],
        "records": res["records"],
        "export": exported,
    }


def cmd_agent(args) -> dict:
    agent = WebAgent(args.base, headless=not args.headed)
    return agent.run(args.text, out=args.out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="web_agent", description="AI 网页信息采集智能体")
    parser.add_argument("--verbose", action="store_true", help="输出调试日志")
    sub = parser.add_subparsers(dest="command", required=True)

    pc = sub.add_parser("collect", help="采集指定网页的字段并导出 JSON")
    pc.add_argument("--base", default="http://127.0.0.1:5099", help="目标站点根地址")
    pc.add_argument("--path", default="/notices", help="目标路径或完整 URL")
    pc.add_argument("--fields", default="", help="要采集的字段，逗号分隔；留空表示采集全部列")
    pc.add_argument("--out", default=None, help="输出文件路径；省略时自动写入 exports/ 目录")
    pc.add_argument("--row-selector", default=None, help="自定义表格行选择器")
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