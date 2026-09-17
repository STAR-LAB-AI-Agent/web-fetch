# -*- coding: utf-8 -*-
"""WebAgent：把自然语言指令编排成「解析计划 → 采集 → 去重 → 导出」的完整流程。

智能体可调用的工具：
- collect_page  ：采集单个页面，按用户要求的字段输出结构化记录
- collect_pages ：多网页采集并合并去重（任务书的可选功能）
- export_result ：把记录导出成 JSON / CSV / Excel（目标文件已存在时先询问是否覆盖）
"""
from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from .dedup import dedup_rows as dedup_rows_fn
from .export import export as export_fn
from .extract import collect as collect_page_fn
from .router import route as route_fn

log = logging.getLogger("web_agent")

SYSTEM_PROMPT = (
    "你是网页信息采集助手。请把用户的自然语言需求转换成 JSON 采集计划，"
    "字段包括 path（目标路径或 URL）、fields（要采集的字段名数组，"
    "取值如 标题/发布时间/发布单位/编号/分类/链接/名称/型号/价格/供应商）、"
    "pages（页码数组，或用 \"all\" 表示多页）、format（json/csv/xlsx）、"
    "dedup_by（需要去重时的字段名，否则为 null）。只输出 JSON。"
)


EMPTY_HINT = ("未采集到任何记录：请确认目标页面确实含有数据，"
              "或用 --kind table/list/item 指定页面结构；"
              "字段名与页面不一致时会置空并记入 missing_fields。")


def _with_page(path: str, page: int) -> str:
    """在路径上附加分页参数。"""
    parts = urlsplit(path)
    query = dict(parse_qsl(parts.query))
    query["page"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def llm_plan(text: str, base_url: str):
    """可选的在线模型解析；未配置密钥或调用失败时返回 None，由规则解析兜底。"""
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI

        client = OpenAI()
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "站点根地址：%s\n需求：%s" % (base_url, text)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        plan = json.loads(resp.choices[0].message.content)
        plan.setdefault("pages", [1])
        plan.setdefault("fields", [])
        plan.setdefault("format", "json")
        plan.setdefault("dedup_by", None)
        plan["action"] = "collect"
        plan["source"] = "llm"
        return plan
    except Exception as exc:  # 网络/额度/格式任何异常都回退，保证离线可用
        log.warning("在线模型解析失败，回退到规则解析：%s", exc)
        return None


class WebAgent:
    def __init__(self, base_url: str = "http://127.0.0.1:5099", headless: bool = True):
        self.base_url = base_url
        self.headless = headless

    # ---------------- 工具 1：单页采集 ----------------
    def collect_page(self, path: str = "/", fields=None, kind: str = "auto",
                     row_selector: str | None = None, page: int | None = None) -> dict:
        if page and page > 1:
            path = _with_page(path, page)
        return collect_page_fn(self.base_url, path, kind=kind, row_selector=row_selector,
                               fields=fields, headless=self.headless)

    # ---------------- 工具 2：多网页采集 + 去重 ----------------
    def collect_pages(self, path: str = "/notices", pages="all", fields=None,
                      dedup_by: str | None = None, max_pages: int = 10) -> dict:
        if pages == "all":
            page_numbers = list(range(1, max_pages + 1))
            stop_when_empty = True
        else:
            page_numbers = list(pages)
            stop_when_empty = False

        pages_data = []
        for num in page_numbers:
            res = self.collect_page(path, fields=fields, page=num)
            if stop_when_empty and res["count"] == 0:
                break
            pages_data.append({"page": num, "records": res["records"]})

        flat = [r for p in pages_data for r in p["records"]]
        kept, removed = dedup_rows_fn(flat, dedup_by) if dedup_by else (flat, 0)
        return {
            "path": path,
            "pages": [p["page"] for p in pages_data],
            "pages_data": pages_data,
            "records": kept,
            "count": len(kept),
            "duplicates_removed": removed,
            "dedup_by": dedup_by,
        }

    # ---------------- 工具 3：导出 ----------------
    def export_result(self, records, fmt: str = "json", path: str | None = None,
                      *, overwrite: bool = False) -> dict:
        if not path:
            os.makedirs("exports", exist_ok=True)
            name = "collect_%s" % __import__("time").strftime("%Y%m%d_%H%M%S")
            path = os.path.join("exports", "%s.%s" % (name, fmt))
        return export_fn(records, fmt, path, overwrite=overwrite)

    # ---------------- 自然语言入口 ----------------
    def run(self, text: str, out: str | None = None, *, overwrite: bool = False,
            kind: str | None = None) -> dict:
        plan = llm_plan(text, self.base_url) or route_fn(text)
        fields = plan.get("fields") or []
        pages = plan.get("pages") or [1]
        fmt = plan.get("format") or "json"
        # 页面结构优先级：命令行显式指定 > 自然语言解析结果 > 自动识别
        page_kind = kind or plan.get("kind") or "auto"
        plan["kind"] = page_kind

        if pages == "all" or (isinstance(pages, list) and len(pages) > 1):
            collected = self.collect_pages(plan["path"], pages, fields, plan.get("dedup_by"))
        else:
            page = pages[0] if isinstance(pages, list) and pages else 1
            single = self.collect_page(plan["path"], fields=fields, page=page, kind=page_kind)
            collected = {
                "path": plan["path"], "pages": [page], "records": single["records"],
                "count": single["count"], "duplicates_removed": 0,
                "dedup_by": plan.get("dedup_by"), "missing_fields": single["missing_fields"],
            }

        exported = self.export_result(collected["records"], fmt, out, overwrite=overwrite)
        result = {
            "ok": True,
            "action": "collect",
            "input": text,
            "plan": plan,
            "count": collected["count"],
            "duplicates_removed": collected.get("duplicates_removed", 0),
            "missing_fields": collected.get("missing_fields", []),
            "records": collected["records"],
            "export": exported,
        }
        if result["count"] == 0:
            result["hint"] = EMPTY_HINT
        return result