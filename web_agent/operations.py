"""Playwright 确定性操作（初版 v1）：仅查询某日可预约时段。

后续迭代会在此基础上扩展 fill_form / submit_form 等提交类操作，
并引入「提交前预览与用户确认」。
"""
from __future__ import annotations

from datetime import date, timedelta


def query_slot(base_url: str, date_str: str = "", headless: bool = True) -> dict:
    """访问 /query 页面，返回精简时段表（不抓取整页 HTML）。"""
    from playwright.sync_api import sync_playwright

    day = date_str or (date.today() + timedelta(days=1)).isoformat()
    url = f"{base_url.rstrip('/')}/query?date={day}"
    rows: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, timeout=15000)
        page.wait_for_selector("table tbody tr")
        for tr in page.query_selector_all("table tbody tr"):
            cells = [c.inner_text().strip() for c in tr.query_selector_all("td")]
            if len(cells) >= 3:
                rows.append({"time": cells[0], "used": cells[1], "status": cells[2]})
        browser.close()
    return {"url": url, "date": day, "slots": rows, "ok": bool(rows)}