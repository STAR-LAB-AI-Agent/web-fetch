# -*- coding: utf-8 -*-
"""字段抽取的单元测试：直接喂入页面原始结构，不启动浏览器。"""
from web_agent.extract import (is_link_field, match_key, records_from_item,
                               records_from_list, records_from_table)

TABLE_RAW = {
    "headers": ["编号", "标题", "发布单位", "发布时间", "分类", "详情"],
    "rows": [
        [{"text": "N-01", "href": ""}, {"text": "通知甲", "href": ""},
         {"text": "网络空间安全学院", "href": ""}, {"text": "2026-09-01", "href": ""},
         {"text": "活动通知", "href": ""}, {"text": "查看", "href": "http://x/notices/N-01"}],
        [{"text": "N-02", "href": ""}, {"text": "通知乙", "href": ""},
         {"text": "教务办公室", "href": ""}, {"text": "2026-09-02", "href": ""},
         {"text": "教学通知", "href": ""}, {"text": "查看", "href": "http://x/notices/N-02"}],
    ],
}


def test_match_key_alias_and_containment():
    assert match_key("价格", ["型号", "参考价", "供应商"]) == "参考价"
    assert match_key("日期", ["发布时间"]) == "发布时间"
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
    records, _ = records_from_table(TABLE_RAW, ["标题", "链接"])
    assert records[1]["链接"] == "http://x/notices/N-02"


def test_table_all_columns_when_fields_omitted():
    records, missing = records_from_table(TABLE_RAW, None)
    assert missing == []
    assert list(records[0].keys()) == TABLE_RAW["headers"]
    assert records[0]["编号"] == "N-01"


def test_table_reports_missing_field():
    records, missing = records_from_table(TABLE_RAW, ["标题", "作者"])
    assert missing == ["作者"]
    assert records[0]["作者"] == ""


def test_list_records_parse_labeled_lines():
    blocks = [{"lines": ["高性能计算服务器", "型号：HS-7020", "参考价：128000 元",
                         "供应商：启元科技", "查看详情"],
               "heading": "高性能计算服务器", "href": "http://x/products/P-01"}]
    records, missing = records_from_list(blocks, ["名称", "型号", "价格", "供应商", "链接"])
    assert missing == []
    assert records[0]["名称"] == "高性能计算服务器"
    assert records[0]["型号"] == "HS-7020"
    assert records[0]["价格"] == "128000 元"
    assert records[0]["链接"] == "http://x/products/P-01"


def test_item_records_from_detail_page():
    raw = {"heading": "关于实习工作的通知", "pairs": {"编号": "N-04", "发布单位": "教务办公室",
                                                       "发布时间": "2026-09-04", "分类": "教学通知"},
           "body": "正文内容", "href": "http://x/files/N-04.pdf"}
    records, missing = records_from_item(raw, ["标题", "发布单位", "正文", "链接"])
    assert missing == []
    assert records[0]["标题"] == "关于实习工作的通知"
    assert records[0]["发布单位"] == "教务办公室"
    assert records[0]["正文"] == "正文内容"
    assert records[0]["链接"] == "http://x/files/N-04.pdf"