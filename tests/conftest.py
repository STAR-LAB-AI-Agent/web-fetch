"""pytest 共享 fixture（v1）：集成测试按需启动真实 HTTP 站点。"""
from __future__ import annotations

import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mock_site import app as mock_app  # noqa: E402


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _Server:
    def __init__(self):
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(
            target=lambda: mock_app.app.run(host="127.0.0.1", port=self.port, debug=False, use_reloader=False),
            daemon=True,
        )

    def start(self, timeout_s: float = 10.0):
        self._thread.start()
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                urllib.request.urlopen(self.base_url + "/", timeout=1)
                return
            except Exception:
                time.sleep(0.15)
        raise RuntimeError("mock site 启动超时")


@pytest.fixture(scope="session")
def mock_server():
    srv = _Server()
    srv.start()
    yield srv