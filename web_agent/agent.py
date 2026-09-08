"""智能体入口（初版 v1）：先打通「查询」意图的端到端闭环。

v1 目标：完成
    用户自然语言 → 智能体 → CLI/Skill → Playwright → 网站 → 结构化结果
一条完整链路。「预约」「填报」两类意图明确返回“后续支持”提示，
留作后续迭代（将配套表单填写、提交前预览与用户确认）。
"""
from __future__ import annotations

import logging
import re
from datetime import date, timedelta

from . import operations

log = logging.getLogger("web_agent")


def _parse_date(text: str) -> str:
    """从文本解析日期：今天/明天/后天/YYYY-MM-DD，默认明天。"""
    if "后天" in text:
        return (date.today() + timedelta(days=2)).isoformat()
    if "明天" in text:
        return (date.today() + timedelta(days=1)).isoformat()
    if "今天" in text:
        return date.today().isoformat()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else (date.today() + timedelta(days=1)).isoformat()


class WebAgent:
    """初版智能体：离线关键词路由，仅支持「查询」意图。"""

    def __init__(self, base_url: str = "http://127.0.0.1:5099", headless: bool = True):
        self.base_url = base_url.rstrip("/")
        self.headless = headless

    def decide(self, text: str) -> dict:
        """自然语言 → 动作规划。v1 仅查询；预约/填报明确提示规划中。"""
        if any(k in text for k in ("查询", "查", "可预约", "时段", "空余", "有空", "看看")):
            return {"tool": "query_slot", "args": {"date": _parse_date(text)}, "intent": "查询"}
        if any(k in text for k in ("预约", "预订", "订位")):
            return {"tool": None, "intent": "预约", "deferred": True, "note": "预约功能将在后续迭代版本提供"}
        if any(k in text for k in ("填报", "反馈", "报修")):
            return {"tool": None, "intent": "填报", "deferred": True, "note": "填报功能将在后续迭代版本提供"}
        return {"tool": None, "intent": "未识别"}

    def execute(self, text: str) -> dict:
        """端到端执行并返回结构化结果。"""
        plan = self.decide(text)
        log.info("decide: %s", plan)
        tool = plan.get("tool")
        if tool == "query_slot":
            res = operations.query_slot(self.base_url, plan["args"].get("date", ""), headless=self.headless)
            res["ok"] = True
            res["input"] = text
            res["plan"] = plan
            return res
        error = plan.get("note", "初版暂不支持该意图，请期待后续迭代版本")
        return {"ok": False, "input": text, "plan": plan, "error": error}