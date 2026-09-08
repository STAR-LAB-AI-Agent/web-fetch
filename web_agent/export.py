# -*- coding: utf-8 -*-
"""采集结果导出：本期只实现 JSON。

JSON 能完整保留结构化数据，便于程序继续处理；CSV / Excel 输出留待后续迭代。
"""
from __future__ import annotations

import json
import os
from typing import Mapping, Sequence

FORMATS = ("json",)


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


def export(rows: Sequence[Mapping[str, object]], fmt: str = "json", path: str | None = None) -> dict:
    """导出采集结果。返回 {format, path, count, columns}。"""
    fmt = (fmt or "json").lower()
    if fmt not in FORMATS:
        raise ValueError("不支持的导出格式：%s（本期支持 %s）" % (fmt, " / ".join(FORMATS)))

    text = to_json_text(rows)
    if path:
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)

    return {
        "format": fmt,
        "path": os.path.abspath(path) if path else None,
        "count": len(rows),
        "columns": columns_of(rows),
    }