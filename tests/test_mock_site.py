"""模拟站点基础行为（v1：查询相关）。"""
from __future__ import annotations

from mock_site.app import app, SLOTS, _slots_for


def test_index_ok():
    rv = app.test_client().get("/")
    assert rv.status_code == 200
    assert "服务预约系统" in rv.get_data(as_text=True)


def test_query_returns_all_slots():
    rv = app.test_client().get("/query?date=2026-09-09")
    assert rv.status_code == 200
    body = rv.get_data(as_text=True)
    for s in SLOTS:
        assert s in body


def test_slots_for_defaults():
    rows = _slots_for("2026-09-09")
    assert len(rows) == len(SLOTS)
    assert all(row["used"] == 0 and "可约" in row["status"] for row in rows)