# -*- coding: utf-8 -*-
"""多网页采集结果去重（任务书第 22 题的可选功能）。

去重策略：默认按用户指定的字段（如“编号”“链接”）判断重复，保留首次出现的
记录；未指定字段时退化为“整行内容相同即视为重复”。
"""
from __future__ import annotations

from typing import Mapping, Sequence


def _row_key(row: Mapping[str, object], key: str):
    for name in (key, key.lower(), key.upper()):
        if name in row:
            return str(row[name]).strip()
    raise KeyError("去重字段不存在：%s（可用字段：%s）" % (key, "、".join(row.keys())))


def dedup_rows(rows: Sequence[Mapping[str, object]], key: str | None = None):
    """返回 (去重后的记录列表, 被移除的条数) 以及每条记录归属的重复次数。"""
    seen = set()
    kept = []
    removed = 0
    for row in rows:
        sig = _row_key(row, key) if key else "|".join(str(v) for v in row.values())
        if sig in seen:
            removed += 1
            continue
        seen.add(sig)
        kept.append(dict(row))
    return kept, removed


def merge_pages(pages: Sequence[Sequence[Mapping[str, object]]], key: str | None = None):
    """把多个页面的采集结果合并，并按 key 去重。"""
    merged = []
    for page_rows in pages:
        merged.extend(dict(r) for r in page_rows)
    return dedup_rows(merged, key)