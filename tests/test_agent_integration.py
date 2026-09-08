"""智能体端到端（v1：仅查询；需 Playwright，未装则整体跳过）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

try:
    import playwright  # noqa: F401
    from web_agent.agent import WebAgent  # noqa: E402
    HAS_PW = True
except Exception:
    HAS_PW = False

pytestmark = pytest.mark.skipif(not HAS_PW, reason="Playwright 未安装，跳过集成测试")


def test_agent_query(mock_server):
    agent = WebAgent(base_url=mock_server.base_url)
    res = agent.execute("查询明天可预约时段")
    assert res["ok"] is True
    assert res["plan"]["tool"] == "query_slot"
    assert len(res["slots"]) == 4


def test_agent_deferred_intent(mock_server):
    agent = WebAgent(base_url=mock_server.base_url)
    res = agent.execute("预约明天9:00，姓名张三")
    assert res["ok"] is False
    assert "后续迭代" in res["error"]