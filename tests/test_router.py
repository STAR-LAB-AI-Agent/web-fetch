# -*- coding: utf-8 -*-
"""离线路由解析的单元测试（纯逻辑，不启动浏览器）。"""
from web_agent import router


def test_detect_path_from_keywords():
    assert router.detect_path("把公告列表的标题采集下来") == "/notices"
    assert router.detect_path("采集通知的标题") == "/notices"


def test_detect_path_explicit_url_wins():
    assert router.detect_path("采集 /notices?page=2 上的标题") == "/notices?page=2"
    assert router.detect_path("采集 http://127.0.0.1:5099/notices 的标题") == "http://127.0.0.1:5099/notices"


def test_detect_fields_follows_order_in_sentence():
    assert router.detect_fields("把发布时间和标题采集下来") == ["发布时间", "标题"]
    assert router.detect_fields("采集编号、标题、发布单位") == ["编号", "标题", "发布单位"]


def test_detect_fields_synonyms():
    assert "链接" in router.detect_fields("把每一条的详情地址也采集下来")
    assert "发布时间" in router.detect_fields("采集发布日期")


def test_detect_fields_empty_when_unspecified():
    assert router.detect_fields("把公告列表采集下来") == []


def test_route_full_plan():
    plan = router.route("采集公告的标题、发布时间和发布单位")
    assert plan["action"] == "collect"
    assert plan["path"] == "/notices"
    assert plan["fields"] == ["标题", "发布时间", "发布单位"]
    assert plan["format"] == "json"
    assert plan["source"] == "rule"