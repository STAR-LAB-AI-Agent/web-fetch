"""命令行入口（初版 v1）：agent 统一入口 + query 单步命令。"""
from __future__ import annotations

import argparse
import json

from . import operations
from .agent import WebAgent


def _out(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="web_agent", description="AI 网页业务操作（初版 v1：仅查询）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("agent", help="自然语言统一入口")
    pa.add_argument("--base", required=True)
    pa.add_argument("--text", required=True)
    pa.add_argument("--headed", action="store_true")

    pq = sub.add_parser("query", help="单步：查询可预约时段")
    pq.add_argument("--base", required=True)
    pq.add_argument("--date", default="")
    pq.add_argument("--headed", action="store_true")

    args = parser.parse_args()
    if args.cmd == "agent":
        _out(WebAgent(base_url=args.base, headless=not args.headed).execute(args.text))
    elif args.cmd == "query":
        _out(operations.query_slot(args.base, args.date, headless=not args.headed))


if __name__ == "__main__":
    main()