# -*- coding: utf-8 -*-
"""本地模拟目标网站的行为测试（Flask 测试客户端，不启动浏览器）。"""


def test_index_lists_entry_points(client):
    html = client.get("/").get_data(as_text=True)
    assert "信息发布平台" in html
    assert "/notices" in html and "/products" in html


def test_notices_first_page(client):
    resp = client.get("/notices")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "N-01" in html and "N-06" in html


def test_notices_bad_page_number_returns_400(client):
    assert client.get("/notices?page=abc").status_code == 400


def test_notices_out_of_range_returns_404(client):
    assert client.get("/notices?page=9").status_code == 404


def test_pagination_overlap_is_reserved_for_dedup_demo(client):
    """第 1 页与第 2 页刻意保留同一条记录，用于演示多网页采集去重。"""
    page1 = client.get("/notices?page=1").get_data(as_text=True)
    page2 = client.get("/notices?page=2").get_data(as_text=True)
    assert "N-06" in page1 and "N-06" in page2


def test_products_page(client):
    html = client.get("/products").get_data(as_text=True)
    assert "高性能计算服务器" in html and "HS-7020" in html


def test_notice_detail(client):
    html = client.get("/notices/N-01").get_data(as_text=True)
    assert "关于开展2026年网络安全宣传周活动的通知" in html
    assert "/files/N-01.pdf" in html


def test_notice_detail_missing_returns_404(client):
    assert client.get("/notices/N-99").status_code == 404


def test_product_detail(client):
    html = client.get("/products/P-03").get_data(as_text=True)
    assert "网络安全审计系统" in html and "恒信安全" in html