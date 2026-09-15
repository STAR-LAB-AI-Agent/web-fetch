# -*- coding: utf-8 -*-
"""采集结果导出：JSON / CSV / Excel。

三种格式的定位：
- JSON：保留完整的结构化数据，便于程序继续处理；
- CSV ：便于用表格软件查看，使用 utf-8-sig 编码以便 Excel 直接打开不乱码；
- XLSX：使用 openpyxl 写入，包含表头样式与列宽设置。
"""
from __future__ import annotations

import csv
import io
import json
import os
from typing import Mapping, Sequence

FORMATS = ("json", "csv", "xlsx")


def columns_of(rows: Sequence[Mapping[str, object]]) -> list:
    """按出现顺序汇总所有列名，容忍不同行字段不一致的情况。"""
    cols = []
    for row in rows:
        for key in row.keys():
            if key not in cols:
                cols.append(key)
    return cols


def to_json_text(rows: Sequence[Mapping[str, object]]) -> str:
    return json.dumps(list(rows), ensure_ascii=False, indent=2)


def to_csv_text(rows: Sequence[Mapping[str, object]]) -> str:
    cols = columns_of(rows)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({c: row.get(c, "") for c in cols})
    return buf.getvalue()


def write_xlsx(rows: Sequence[Mapping[str, object]], path: str) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    cols = columns_of(rows)
    wb = Workbook()
    ws = wb.active
    ws.title = "采集结果"
    ws.append(cols)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="EEF1F6")
        cell.alignment = Alignment(horizontal="center")
    for row in rows:
        ws.append([str(row.get(c, "")) for c in cols])
    for i, col in enumerate(cols, start=1):
        width = max([len(str(col))] + [len(str(r.get(col, ""))) for r in rows]) if rows else len(str(col))
        ws.column_dimensions[get_column_letter(i)].width = min(60, max(10, width * 1.4))
    wb.save(path)


def export(rows: Sequence[Mapping[str, object]], fmt: str = "json", path: str | None = None) -> dict:
    """导出采集结果。返回 {format, path, count, columns}。"""
    fmt = (fmt or "json").lower()
    if fmt not in FORMATS:
        raise ValueError("不支持的导出格式：%s（可选 %s）" % (fmt, " / ".join(FORMATS)))

    if fmt == "json":
        text = to_json_text(rows)
        if path:
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(text)
    elif fmt == "csv":
        text = to_csv_text(rows)
        if path:
            with open(path, "w", encoding="utf-8-sig", newline="") as fp:
                fp.write(text)
    else:
        if not path:
            raise ValueError("导出 Excel 必须指定输出文件路径")
        write_xlsx(rows, path)

    return {
        "format": fmt,
        "path": os.path.abspath(path) if path else None,
        "count": len(rows),
        "columns": columns_of(rows),
    }