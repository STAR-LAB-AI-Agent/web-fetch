# -*- coding: utf-8 -*-
"""导出功能的单元测试：JSON / CSV / Excel。"""
import json

import pytest
from openpyxl import load_workbook

from web_agent.export import columns_of, export, to_csv_text, to_json_text

ROWS = [{"标题": "甲", "发布时间": "2026-09-01"},
        {"标题": "乙", "发布时间": "2026-09-02"}]


def test_columns_of_union_keeps_order():
    assert columns_of([{"a": 1}, {"b": 2, "a": 3}]) == ["a", "b"]


def test_to_json_text_is_utf8_readable():
    data = json.loads(to_json_text(ROWS))
    assert data[0]["标题"] == "甲"
    assert len(data) == 2


def test_to_csv_text_has_header_and_rows():
    lines = to_csv_text(ROWS).strip().splitlines()
    assert lines[0] == "标题,发布时间"
    assert lines[1].startswith("甲,")


def test_export_json_file(tmp_path):
    path = tmp_path / "out.json"
    info = export(ROWS, "json", str(path))
    assert info["count"] == 2
    assert info["columns"] == ["标题", "发布时间"]
    assert json.loads(path.read_text(encoding="utf-8"))[1]["标题"] == "乙"


def test_export_csv_file_is_excel_friendly(tmp_path):
    path = tmp_path / "out.csv"
    export(ROWS, "csv", str(path))
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")  # utf-8-sig


def test_export_xlsx_roundtrip(tmp_path):
    path = tmp_path / "out.xlsx"
    export(ROWS, "xlsx", str(path))
    sheet = load_workbook(path).active
    assert [c.value for c in sheet[1]] == ["标题", "发布时间"]
    assert sheet["A2"].value == "甲"
    assert sheet.max_row == 3


def test_export_rejects_unknown_format():
    with pytest.raises(ValueError):
        export(ROWS, "yaml", None)


def test_xlsx_requires_output_path():
    with pytest.raises(ValueError):
        export(ROWS, "xlsx", None)