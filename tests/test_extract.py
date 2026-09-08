# -*- coding: utf-8 -*-
"""字段抽取的单元测试：直接喂入页面原始结构，不启动浏览器。"""
from web_agent.extract import is_link_field, match_key, records_from_table

TABLE_RAW = {
    "headers": ["编号", "标题", "发布单位", "发布时间", "分类"],
    "rows": [
        [{"text": "N-01", "href": ""}, {"text": "通知甲", "href": ""},
         {"text": "网络空间安全学院", "href": ""}, {"text": "2026-09-01", "href": ""},
         {"text": "活动通知", "href": ""}],
        [{"text": "N-02", "href": ""}, {"text": "通知乙", "href": ""},
         {"text": "教务办公室", "href": ""}, {"text": "2026-09-02", "href": ""},
         {"text": "教学通知", "href": ""}],
    ],
}


def test_match_key_alias_and_containment():
    assert match_key("日期", ["发布时间"]) == "发布时间"
    assert match_key("单位", ["发布单位"]) == "发布单位"
    assert match_key("不存在的字段", ["标题"]) is None


def test_is_link_field():
    assert is_link_field("链接") and is_link_field("详情")
    assert not is_link_field("标题")


def test_table_field_mapping():
    records, missing = records_from_table(TABLE_RAW, ["标题", "发布时间"])
    assert missing == []
    assert records[0] == {"标题": "通知甲", "发布时间": "2026-09-01"}
    assert len(records) == 2


def test_table_link_field_uses_href():
    raw = {"headers": ["标题", "详情"],
           "rows": [[{"text": "通知甲", "href": ""},
                     {"text": "查看", "href": "http://x/notices/N-01"}]]}
    records, _ = records_from_table(raw, ["标题", "链接"])
    assert records[0]["链接"] == "http://x/notices/N-01"


def test_table_all_columns_when_fields_omitted():
    records, missing = records_from_table(TABLE_RAW, None)
    assert missing == []
    assert list(records[0].keys()) == TABLE_RAW["headers"]
    assert records[0]["编号"] == "N-01"


def test_table_reports_missing_field():
    records, missing = records_from_table(TABLE_RAW, ["标题", "作者"])
    assert missing == ["作者"]
    assert records[0]["作者"] == ""