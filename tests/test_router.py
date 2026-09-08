"""初版路由：查询可用；预约/填报明确返回“后续支持”。"""
from __future__ import annotations

from web_agent.agent import WebAgent


def test_route_query_intent():
    agent = WebAgent(base_url="http://x")
    plan = agent.decide("查询明天可预约时段")
    assert plan["tool"] == "query_slot"
    assert plan["args"]["date"]


def test_route_book_deferred():
    agent = WebAgent(base_url="http://x")
    plan = agent.decide("预约明天9:00，姓名张三")
    assert plan.get("tool") is None
    assert plan.get("deferred") is True


def test_route_report_deferred():
    agent = WebAgent(base_url="http://x")
    plan = agent.decide("填报打印机使用反馈")
    assert plan.get("tool") is None
    assert plan.get("deferred") is True