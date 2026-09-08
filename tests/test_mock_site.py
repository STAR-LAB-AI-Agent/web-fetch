# -*- coding: utf-8 -*-
"""本地模拟目标网站的行为测试（Flask 测试客户端，不启动浏览器）。"""


def test_index_lists_entry_points(client):
    html = client.get("/").get_data(as_text=True)
    assert "信息发布平台" in html
    assert "/notices" in html


def test_notices_table(client):
    resp = client.get("/notices")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "N-01" in html and "N-12" in html


def test_notices_table_headers(client):
    html = client.get("/notices").get_data(as_text=True)
    for col in ("编号", "标题", "发布单位", "发布时间", "分类"):
        assert col in html