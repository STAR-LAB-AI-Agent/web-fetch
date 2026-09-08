# -*- coding: utf-8 -*-
"""自然语言 → 采集计划：解析目标页面与要采集的字段。

本期（v1）只覆盖「表格列表页 → 指定字段 → JSON」这一条闭环，因此这里只负责识别
目标页面与字段；页数、去重字段等参数留待后续迭代。默认不依赖在线大模型：用关键词
与别名表完成识别，保证无网络环境下也能完整演示。
"""
from __future__ import annotations

import re

# 目标页面关键词 -> 路径
TARGET_KEYWORDS = (
    ("/notices", ("公告", "通知", "公示", "新闻", "列表页")),
)

# 用户说法 -> 规范字段名（按出现位置排序后作为输出列顺序）
FIELD_TRIGGERS = (
    ("编号", ("编号", "序号")),
    ("标题", ("标题", "题目")),
    ("发布单位", ("发布单位", "发布部门", "单位", "来源")),
    ("发布时间", ("发布时间", "发布日期", "日期", "时间")),
    ("分类", ("分类", "类别", "类型")),
    ("链接", ("链接", "详情", "网址", "地址", "url", "URL")),
    ("正文", ("正文", "摘要", "内容")),
)

DEFAULT_PATH = "/notices"
DEFAULT_FORMAT = "json"


def detect_path(text: str, default: str = DEFAULT_PATH) -> str:
    m = re.search(r"(https?://[^\s，,。]+|/[A-Za-z0-9_\-/]+(?:\?[^\s，,。]+)?)", text)
    if m:
        return m.group(1)
    for path, words in TARGET_KEYWORDS:
        if any(w in text for w in words):
            return path
    return default


def detect_fields(text: str) -> list:
    hits = []
    for canonical, triggers in FIELD_TRIGGERS:
        pos = None
        for trig in triggers:
            idx = text.find(trig)
            if idx >= 0 and (pos is None or idx < pos):
                pos = idx
        if pos is not None:
            hits.append((pos, canonical))
    hits.sort(key=lambda x: x[0])
    return [name for _, name in hits]


def route(text: str) -> dict:
    """把一句自然语言解析成采集计划。"""
    text = (text or "").strip()
    return {
        "action": "collect",
        "path": detect_path(text),
        "fields": detect_fields(text),
        # 导出格式本期固定为 JSON，CSV / Excel 留待后续迭代
        "format": DEFAULT_FORMAT,
        "source": "rule",
    }