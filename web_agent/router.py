# -*- coding: utf-8 -*-
"""自然语言 → 采集计划：解析目标页面、字段、页数与导出格式。

默认不依赖在线大模型：用关键词与别名表完成识别，保证无网络环境下也能完整
演示；若配置了 OPENAI_API_KEY，则可选用在线模型解析（见 agent.py），失败时
自动回退到本模块的规则解析。
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# 目标页面关键词 -> 路径
TARGET_KEYWORDS = (
    ("/notices", ("公告", "通知", "公示", "新闻", "列表页")),
    ("/products", ("设备", "产品", "商品", "器材", "型号")),
)

# 用户说法 -> 规范字段名（按出现位置排序后作为输出列顺序）
FIELD_TRIGGERS = (
    ("编号", ("编号", "序号")),
    ("标题", ("标题", "题目")),
    ("名称", ("名称", "品名", "设备名")),
    ("型号", ("型号", "规格")),
    ("分类", ("分类", "类别", "类型")),
    ("发布单位", ("发布单位", "发布部门", "单位", "来源")),
    ("发布时间", ("发布时间", "发布日期", "日期", "时间")),
    ("价格", ("价格", "参考价", "报价", "单价")),
    ("供应商", ("供应商", "厂商", "厂家")),
    ("链接", ("链接", "详情", "网址", "地址", "url", "URL")),
    ("正文", ("正文", "摘要", "内容")),
)

# 表达「只看某一条 / 详情页」的说法
DETAIL_KEYWORDS = ("详情", "这条", "该条", "某一条", "单条",
                   "这个公告", "该公告", "这个设备", "该设备",
                   "这个产品", "该产品")

CN_NUM = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6,
          "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6}


def detect_path(text: str, default: str = "/notices") -> str:
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


def detect_format(text: str, default: str = "json") -> str:
    low = text.lower()
    if "excel" in low or "xlsx" in low or "表格" in text:
        return "xlsx"
    if "csv" in low:
        return "csv"
    if "json" in low:
        return "json"
    return default


def detect_pages(text: str) -> list:
    """返回页码列表；'all' 表示由调用方逐页探测直到没有数据。"""
    m = re.search(r"前([一二两三四五六\d]+)页", text)
    if m:
        n = CN_NUM.get(m.group(1), 1)
        return list(range(1, max(1, n) + 1))
    m = re.search(r"第([一二两三四五六\d]+)页", text)
    if m:
        return [CN_NUM.get(m.group(1), 1)]
    if any(w in text for w in ("全部", "所有", "多页", "各页", "所有页")):
        return "all"
    return [1]


def detect_dedup(text: str, fields: list):
    if "去重" not in text:
        return None
    for cand in ("链接", "编号", "标题", "名称"):
        if cand in fields:
            return cand
    return "链接"


def _path_only(path: str) -> str:
    """去掉协议与域名，只留路径部分。"""
    if path.startswith("http://") or path.startswith("https://"):
        return urlparse(path).path or "/"
    return path


def detect_kind(text: str, path: str) -> str:
    """判断目标页面结构；返回 auto 时交给采集层自动识别。

    两类信号指向详情页：话里出现「详情 / 这条 / 单条」等说法，
    或者目标路径是 /notices/N-01 这种两段式（列表页只有一段）。
    """
    if any(w in text for w in DETAIL_KEYWORDS):
        return "item"
    if _path_only(path).rstrip("/").count("/") >= 2:
        return "item"
    return "auto"


def route(text: str) -> dict:
    """把一句自然语言解析成采集计划。"""
    text = (text or "").strip()
    fields = detect_fields(text)
    path = detect_path(text)
    plan = {
        "action": "collect",
        "path": path,
        "fields": fields,
        "pages": detect_pages(text),
        "format": detect_format(text),
        "dedup_by": detect_dedup(text, fields),
        "kind": detect_kind(text, path),
        "source": "rule",
    }
    return plan