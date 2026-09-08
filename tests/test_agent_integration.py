# -*- coding: utf-8 -*-
"""采集流程的端到端测试（需要 Playwright 浏览器内核）。"""
import json

import pytest

from web_agent import WebAgent
from web_agent.extract import collect

pytestmark = pytest.mark.usefixtures("need_browser")


def test_collect_notice_list_fields(base_url):
    res = collect(base_url, "/notices", fields=["标题", "发布时间", "发布单位"])
    assert res["missing_fields"] == []
    assert res["count"] == 12
    assert all(r["标题"] for r in res["records"])
    assert res["records"][0]["发布单位"] == "网络空间安全学院"


def test_all_columns_when_fields_omitted(base_url):
    res = collect(base_url, "/notices")
    assert list(res["records"][0].keys()) == ["编号", "标题", "发布单位", "发布时间", "分类"]


def test_natural_language_export_json(base_url, tmp_path):
    out = tmp_path / "notices.json"
    result = WebAgent(base_url).run("采集公告的标题、发布时间和发布单位", out=str(out))
    assert result["ok"] is True
    assert result["plan"]["source"] == "rule"
    assert result["plan"]["path"] == "/notices"
    assert result["count"] == 12
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 12
    assert list(data[0].keys()) == ["标题", "发布时间", "发布单位"]