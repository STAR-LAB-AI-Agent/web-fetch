# -*- coding: utf-8 -*-
"""离线路由解析的单元测试（纯逻辑，不启动浏览器）。"""
from web_agent import router


def test_detect_path_from_keywords():
    assert router.detect_path("把公告列表的标题导出来") == "/notices"
    assert router.detect_path("采集设备列表的型号和参考价") == "/products"


def test_detect_path_explicit_url_wins():
    assert router.detect_path("采集 /notices?page=2 上的标题") == "/notices?page=2"
    assert router.detect_path("采集 http://127.0.0.1:5099/products 的名称") == "http://127.0.0.1:5099/products"


def test_detect_fields_follows_order_in_sentence():
    assert router.detect_fields("把发布时间和标题导出来") == ["发布时间", "标题"]
    assert router.detect_fields("采集编号、标题、发布单位") == ["编号", "标题", "发布单位"]


def test_detect_fields_synonyms():
    assert "价格" in router.detect_fields("采集所有设备的报价")
    assert "链接" in router.detect_fields("把每一条的详情地址也采集下来")


def test_detect_fields_empty_when_unspecified():
    assert router.detect_fields("把公告列表采集下来") == []


def test_detect_format():
    assert router.detect_format("导出成 Excel") == "xlsx"
    assert router.detect_format("导出成 csv 文件") == "csv"
    assert router.detect_format("输出 json") == "json"
    assert router.detect_format("随便看看") == "json"


def test_detect_pages():
    assert router.detect_pages("前两页公告") == [1, 2]
    assert router.detect_pages("只看第2页") == [2]
    assert router.detect_pages("全部公告") == "all"
    assert router.detect_pages("公告列表") == [1]


def test_detect_dedup_requires_keyword():
    assert router.detect_dedup("采集公告并去重", ["标题", "链接"]) == "链接"
    assert router.detect_dedup("采集公告并去重", ["编号", "标题"]) == "编号"
    assert router.detect_dedup("采集公告", ["链接"]) is None


def test_route_full_plan():
    plan = router.route("把前两页公告的标题、发布时间和链接导出成 Excel，并去重")
    assert plan["action"] == "collect"
    assert plan["path"] == "/notices"
    assert plan["fields"] == ["标题", "发布时间", "链接"]
    assert plan["pages"] == [1, 2]
    assert plan["format"] == "xlsx"
    assert plan["dedup_by"] == "链接"
    assert plan["source"] == "rule"