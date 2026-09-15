# -*- coding: utf-8 -*-
"""多网页结果去重的单元测试（任务书可选功能）。"""
import pytest

from web_agent.dedup import dedup_rows, merge_pages

ROWS = [{"编号": "N-06", "标题": "甲"}, {"编号": "N-07", "标题": "乙"}, {"编号": "N-06", "标题": "甲"}]


def test_dedup_by_key_keeps_first_occurrence():
    kept, removed = dedup_rows(ROWS, "编号")
    assert removed == 1
    assert [r["编号"] for r in kept] == ["N-06", "N-07"]


def test_dedup_without_key_uses_whole_row():
    kept, removed = dedup_rows([{"a": 1}, {"a": 1}, {"a": 2}])
    assert removed == 1
    assert len(kept) == 2


def test_dedup_unknown_key_raises():
    with pytest.raises(KeyError):
        dedup_rows(ROWS, "编号x")


def test_merge_pages_concatenates_then_dedups():
    kept, removed = merge_pages([[{"链接": "a"}], [{"链接": "a"}, {"链接": "b"}]], "链接")
    assert removed == 1
    assert [r["链接"] for r in kept] == ["a", "b"]