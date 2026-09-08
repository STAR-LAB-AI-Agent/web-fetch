# -*- coding: utf-8 -*-
"""导出功能的单元测试：JSON。"""
import json

import pytest

from web_agent.export import columns_of, export, to_json_text

ROWS = [{"标题": "甲", "发布时间": "2026-09-01"},
        {"标题": "乙", "发布时间": "2026-09-02"}]


def test_columns_of_union_keeps_order():
    assert columns_of([{"a": 1}, {"b": 2, "a": 3}]) == ["a", "b"]


def test_to_json_text_is_utf8_readable():
    data = json.loads(to_json_text(ROWS))
    assert data[0]["标题"] == "甲"
    assert len(data) == 2


def test_export_json_file(tmp_path):
    path = tmp_path / "out.json"
    info = export(ROWS, "json", str(path))
    assert info["count"] == 2
    assert info["columns"] == ["标题", "发布时间"]
    assert json.loads(path.read_text(encoding="utf-8"))[1]["标题"] == "乙"


def test_export_without_path_returns_no_file():
    info = export(ROWS, "json", None)
    assert info["path"] is None
    assert info["count"] == 2


def test_export_rejects_unknown_format():
    with pytest.raises(ValueError):
        export(ROWS, "yaml", None)