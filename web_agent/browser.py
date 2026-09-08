# -*- coding: utf-8 -*-
"""Playwright 浏览器上下文管理：统一超时、UA 与 headless 行为。

采集任务对“确定性”要求较高，因此这里不引入随机等待，只设置统一的超时与
语言环境，保证同一页面在多次运行中得到一致结果。
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from urllib.parse import urljoin

log = logging.getLogger("web_agent")

DEFAULT_TIMEOUT_MS = 15000
USER_AGENT = "Mozilla/5.0 (compatible; CourseCollectAgent/1.0)"


def normalize_url(base_url: str, path: str = "/") -> str:
    """把相对路径拼到站点根地址上；已经是完整 URL 的直接返回。"""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


@contextmanager
def browser_context(headless: bool = True):
    """打开一个浏览器上下文；退出时自动关闭，避免进程残留。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(user_agent=USER_AGENT, locale="zh-CN")
        try:
            yield ctx
        finally:
            ctx.close()
            browser.close()