# -*- coding: utf-8 -*-
"""WebAgent：把自然语言指令编排成「解析计划 → 采集 → 导出」的完整流程。

本期（v1）智能体可调用的工具：
- collect_page  ：采集单个页面，按用户要求的字段输出结构化记录
- export_result ：把记录导出成 JSON
"""
from __future__ import annotations

import json
import logging
import os

from .export import export as export_fn
from .extract import collect as collect_page_fn
from .router import route as route_fn

log = logging.getLogger("web_agent")

SYSTEM_PROMPT = (
    "你是网页信息采集助手。请把用户的自然语言需求转换成 JSON 采集计划，"
    "字段包括 path（目标路径或 URL）、fields（要采集的字段名数组，"
    "取值如 标题/发布时间/发布单位/编号/分类/链接）。只输出 JSON。"
)


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
        plan.setdefault("fields", [])
        plan.setdefault("path", "/notices")
        plan["action"] = "collect"
        plan["format"] = "json"
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
    def collect_page(self, path: str = "/", fields=None,
                     row_selector: str | None = None) -> dict:
        return collect_page_fn(self.base_url, path, row_selector=row_selector,
                               fields=fields, headless=self.headless)

    # ---------------- 工具 2：导出 ----------------
    def export_result(self, records, fmt: str = "json", path: str | None = None) -> dict:
        if not path:
            os.makedirs("exports", exist_ok=True)
            name = "collect_%s" % __import__("time").strftime("%Y%m%d_%H%M%S")
            path = os.path.join("exports", "%s.%s" % (name, fmt))
        return export_fn(records, fmt, path)

    # ---------------- 自然语言入口 ----------------
    def run(self, text: str, out: str | None = None) -> dict:
        plan = llm_plan(text, self.base_url) or route_fn(text)
        fields = plan.get("fields") or []
        fmt = plan.get("format") or "json"

        collected = self.collect_page(plan["path"], fields=fields)
        exported = self.export_result(collected["records"], fmt, out)
        return {
            "ok": True,
            "action": "collect",
            "input": text,
            "plan": plan,
            "count": collected["count"],
            "missing_fields": collected["missing_fields"],
            "records": collected["records"],
            "export": exported,
        }