# -*- coding: utf-8 -*-
"""字段抽取核心：把「指定网页 + 用户要求的字段」变成结构化行记录。

支持两类目标页面结构：
1. table —— 表头 + 数据行（如公告列表），列名自动取 thead 中的表头；
2. list  —— 重复的卡片/条目块（如设备列表），块内按「标签：值」解析字段；
3. item  —— 单条记录的详情页。

抽取结果统一为 list[dict]，键为字段名，可直接交给 export 模块输出 JSON/CSV/Excel。
"""
from __future__ import annotations

import logging

from .browser import DEFAULT_TIMEOUT_MS, normalize_url, browser_context

log = logging.getLogger("web_agent")

# 用户可能说出来的字段名 -> 页面上的实际列名/标签
FIELD_ALIASES = {
    "标题": ["标题", "题目", "名称", "公告标题", "正文标题"],
    "名称": ["名称", "标题", "品名", "设备名称"],
    "编号": ["编号", "序号", "id"],
    "发布时间": ["发布时间", "发布日期", "日期", "时间"],
    "发布单位": ["发布单位", "单位", "发布部门", "来源", "部门"],
    "分类": ["分类", "类别", "类型"],
    "链接": ["链接", "详情", "地址", "网址", "url", "附件"],
    "型号": ["型号", "规格"],
    "价格": ["价格", "参考价", "报价", "单价"],
    "供应商": ["供应商", "厂商", "厂家"],
    "正文": ["正文", "内容", "摘要", "说明"],
}

LINK_FIELDS = ("链接", "详情", "地址", "网址", "附件", "url", "URL", "link")

TABLE_ROW_SELECTOR = "table tbody tr"
LIST_ROW_CANDIDATES = (".card", "article", "li.entry", "li")

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

JS_LIST = """
(sel) => {
  const blocks = Array.from(document.querySelectorAll(sel));
  return blocks.map(b => {
    const heading = b.querySelector('h1,h2,h3,h4');
    const a = b.querySelector('a[href]');
    return {
      lines: (b.innerText || '').split('\\n').map(s => s.trim()).filter(Boolean),
      heading: heading ? (heading.innerText || '').trim() : '',
      href: a ? a.href : ''
    };
  });
}
"""

JS_ITEM = """
() => {
  const pairs = {};
  Array.from(document.querySelectorAll('dl')).forEach(list => {
    const kids = Array.from(list.children);
    for (let i = 0; i < kids.length; i++) {
      if (kids[i].tagName === 'DT' && kids[i + 1] && kids[i + 1].tagName === 'DD') {
        pairs[(kids[i].innerText || '').trim()] = (kids[i + 1].innerText || '').trim();
      }
    }
  });
  const h2 = document.querySelector('h2');
  const body = document.querySelector('p.summary');
  const a = document.querySelector('a[href$=".pdf"], a[href^="/files/"]');
  return {
    heading: h2 ? (h2.innerText || '').trim() : '',
    pairs: pairs,
    body: body ? (body.innerText || '').trim() : '',
    href: a ? a.href : ''
  };
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
    """把用户说法（如“发布时间”“价格”）匹配到页面上的实际列名/标签。"""
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


def records_from_list(raw_blocks, fields=None) -> tuple:
    parsed = []
    for block in raw_blocks:
        rec = {}
        for line in block.get("lines", []):
            for sep in ("：", ":"):
                if sep in line:
                    key, value = line.split(sep, 1)
                    rec[key.strip()] = value.strip()
                    break
        if block.get("heading"):
            rec.setdefault("名称", block["heading"])
            rec.setdefault("标题", block["heading"])
        if block.get("href"):
            rec.setdefault("链接", block["href"])
        parsed.append(rec)

    available = []
    for rec in parsed:
        for key in rec:
            if key not in available:
                available.append(key)

    wanted = list(fields) if fields else list(available)
    missing, plan = [], []
    for name in wanted:
        real = match_key(name, available)
        if real is None:
            missing.append(name)
        plan.append((name, real))

    records = []
    for rec in parsed:
        records.append({name: (rec.get(real, "") if real else "") for name, real in plan})
    return records, missing


def records_from_item(raw: dict, fields=None) -> tuple:
    available = list((raw.get("pairs") or {}).keys())
    if raw.get("heading"):
        available += ["标题", "名称"]
    if raw.get("body"):
        available += ["正文", "摘要"]
    if raw.get("href"):
        available += ["链接", "附件"]

    wanted = list(fields) if fields else available
    missing, plan = [], []
    for name in wanted:
        real = match_key(name, available)
        if real is None:
            missing.append(name)
        plan.append((name, real))

    rec = {}
    for name, real in plan:
        if real is None:
            rec[name] = ""
        elif real in ("标题", "名称") and raw.get("heading"):
            rec[name] = raw["heading"]
        elif real in ("正文", "摘要") and raw.get("body"):
            rec[name] = raw["body"]
        elif real in ("链接", "附件") and raw.get("href"):
            rec[name] = raw["href"]
        else:
            rec[name] = (raw.get("pairs") or {}).get(real, "")
    return [rec], missing


def collect(base_url: str, path: str = "/", *, kind: str = "auto", row_selector: str | None = None,
            fields=None, headless: bool = True) -> dict:
    """采集指定网页，按 fields 抽取字段，返回结构化结果。"""
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
            return {"url": url, "page_title": title, "kind": kind, "row_selector": row_selector,
                    "headers": [], "records": [], "missing_fields": list(fields or []),
                    "count": 0, "status": status}

        if kind == "auto":
            has_table = page.evaluate("() => !!document.querySelector('table tbody tr')")
            kind = "table" if has_table else "list"

        if kind == "table":
            raw = page.evaluate(JS_TABLE, row_selector or TABLE_ROW_SELECTOR)
            records, missing = records_from_table(raw, fields)
            headers = raw.get("headers") or []
        elif kind == "list":
            selector = row_selector
            if not selector:
                for cand in LIST_ROW_CANDIDATES:
                    if page.evaluate("(s) => document.querySelectorAll(s).length >= 2", cand):
                        selector = cand
                        break
            if not selector:
                log.warning("未在页面上找到可重复的列表块，跳过采集：%s", url)
                return {"url": url, "page_title": title, "kind": kind, "row_selector": None,
                        "headers": [], "records": [], "missing_fields": list(fields or []),
                        "count": 0, "status": status}
            raw = page.evaluate(JS_LIST, selector)
            records, missing = records_from_list(raw, fields)
            headers = []
        elif kind == "item":
            raw = page.evaluate(JS_ITEM)
            records, missing = records_from_item(raw, fields)
            headers = []
        else:
            raise ValueError("不支持的目标结构：%s（可选 table / list / item / auto）" % kind)

    return {
        "url": url,
        "page_title": title,
        "kind": kind,
        "row_selector": row_selector,
        "headers": headers,
        "records": records,
        "missing_fields": missing,
        "count": len(records),
        "status": status,
    }