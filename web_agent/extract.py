# -*- coding: utf-8 -*-
"""字段抽取核心：把「指定网页 + 用户要求的字段」变成结构化行记录。

本期（v1）覆盖表格类目标页面（表头 + 数据行，如公告列表）：列名自动取 thead 中的
表头，用户说法按同义词映射到实际列名。抽取结果统一为 list[dict]，键为字段名，可以
直接交给 export 模块输出 JSON。卡片列表页与详情页留待后续迭代。
"""
from __future__ import annotations

import logging

from .browser import DEFAULT_TIMEOUT_MS, normalize_url, browser_context

log = logging.getLogger("web_agent")

# 用户可能说出来的字段名 -> 页面上的实际列名
FIELD_ALIASES = {
    "标题": ["标题", "题目", "名称", "公告标题", "正文标题"],
    "名称": ["名称", "标题", "品名", "设备名称"],
    "编号": ["编号", "序号", "id"],
    "发布时间": ["发布时间", "发布日期", "日期", "时间"],
    "发布单位": ["发布单位", "单位", "发布部门", "来源", "部门"],
    "分类": ["分类", "类别", "类型"],
    "链接": ["链接", "详情", "地址", "网址", "url", "附件"],
    "正文": ["正文", "内容", "摘要", "说明"],
}

LINK_FIELDS = ("链接", "详情", "地址", "网址", "附件", "url", "URL", "link")

TABLE_ROW_SELECTOR = "table tbody tr"

JS_TABLE = """
(sel) => {
  const rows = Array.from(document.querySelectorAll(sel));
  const out = {headers: [], rows: []};
  if (!rows.length) return out;
  const table = rows[0].closest('table');
  if (table) {
    out.headers = Array.from(table.querySelectorAll('thead th')).map(th => (th.innerText || '').trim());
  }
  out.rows = rows.map(tr => Array.from(tr.querySelectorAll('td')).map(td => {
    const a = td.querySelector('a[href]');
    return {text: (td.innerText || '').trim(), href: a ? a.href : ''};
  }));
  return out;
}
"""


def is_link_field(name: str) -> bool:
    return any(token in name for token in LINK_FIELDS)


def _candidates(name: str) -> list:
    """把用户说法展开成候选列名：自身 + 别名表给出的同义说法。"""
    cands = [name]
    if name in FIELD_ALIASES:
        cands += FIELD_ALIASES[name]
    for canonical, aliases in FIELD_ALIASES.items():
        if name in aliases and canonical not in cands:
            cands.append(canonical)
            cands += [a for a in aliases if a not in cands]
    return cands


def match_key(name: str, available) -> str | None:
    """把用户说法（如“发布时间”“单位”）匹配到页面上的实际列名。"""
    candidates = _candidates(name)
    for cand in candidates:
        if cand in available:
            return cand
    for cand in candidates:
        for real in available:
            if cand and (cand in real or real in cand):
                return real
    return None


def records_from_table(raw: dict, fields=None) -> tuple:
    headers = list(raw.get("headers") or [])
    rows = raw.get("rows") or []
    if not headers and rows:
        headers = ["列%d" % (i + 1) for i in range(len(rows[0]))]

    wanted = list(fields) if fields else list(headers)
    missing = []
    plan = []
    for name in wanted:
        real = match_key(name, headers) if headers else None
        if real is None:
            missing.append(name)
            plan.append((name, None, is_link_field(name)))
        else:
            plan.append((name, headers.index(real), is_link_field(name)))

    records = []
    for cells in rows:
        rec = {}
        for name, idx, link in plan:
            if idx is None or idx >= len(cells):
                rec[name] = ""
            elif link and cells[idx].get("href"):
                rec[name] = cells[idx]["href"]
            else:
                rec[name] = cells[idx].get("text", "")
        records.append(rec)
    return records, missing


def collect(base_url: str, path: str = "/", *, row_selector: str | None = None,
            fields=None, headless: bool = True) -> dict:
    """采集指定网页的表格，按 fields 抽取字段，返回结构化结果。"""
    url = normalize_url(base_url, path)
    with browser_context(headless=headless) as ctx:
        page = ctx.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT_MS)
        log.info("collect: %s", url)
        response = page.goto(url, wait_until="domcontentloaded")
        status = response.status if response is not None else 0
        title = page.title()
        if status >= 400:
            log.warning("目标页面返回 %s，跳过采集：%s", status, url)
            return {"url": url, "page_title": title, "row_selector": row_selector,
                    "headers": [], "records": [], "missing_fields": list(fields or []),
                    "count": 0, "status": status}

        raw = page.evaluate(JS_TABLE, row_selector or TABLE_ROW_SELECTOR)
        records, missing = records_from_table(raw, fields)
        headers = raw.get("headers") or []

    return {
        "url": url,
        "page_title": title,
        "row_selector": row_selector,
        "headers": headers,
        "records": records,
        "missing_fields": missing,
        "count": len(records),
        "status": status,
    }