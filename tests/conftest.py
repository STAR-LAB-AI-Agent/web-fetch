# -*- coding: utf-8 -*-
"""测试公共夹具：启动本地模拟站点、统一关闭在线模型、按需跳过浏览器用例。"""
from __future__ import annotations

import os
import sys
import threading

import pytest
from werkzeug.serving import make_server

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 固定走离线规则解析，保证测试不依赖外部模型、结果可复现
os.environ.pop("OPENAI_API_KEY", None)


@pytest.fixture(scope="session")
def base_url():
    """在随机端口启动本地模拟站点，整个测试会话共用一个实例。"""
    from mock_site.app import app

    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:%d" % server.server_port
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def need_browser():
    """浏览器不可用时跳过对应用例（未执行 playwright install 的环境）。"""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            browser.close()
    except Exception as exc:  # pragma: no cover - 取决于本地环境
        pytest.skip("Playwright 浏览器内核不可用：%s" % exc)


@pytest.fixture()
def client():
    """Flask 测试客户端，用于不启动浏览器的站点逻辑校验。"""
    from mock_site.app import app

    return app.test_client()