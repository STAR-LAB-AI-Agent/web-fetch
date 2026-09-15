# -*- coding: utf-8 -*-
"""本地模拟目标网站 —— 供《智能体开发实战》第 22 题“AI 网页信息采集”使用。

设计要点：
- 数据固定在内存中，可重复、可预期，便于自动化测试与结果复现。
- 提供两类目标页面：公告列表（表格结构）与设备列表（卡片结构），各有详情页，
  用于演示“从指定网页采集用户要求的字段”。
- 公告列表带分页，且第 1 页与第 2 页之间刻意保留 1 条重复记录（N-06），
  用于演示可选功能“多网页结果去重”。
"""
from flask import Flask, render_template, abort, request

app = Flask(__name__)

NOTICES = [
    {"id": "N-01", "title": "关于开展2026年网络安全宣传周活动的通知", "unit": "网络空间安全学院", "date": "2026-09-01", "category": "活动通知", "summary": "为提升师生网络安全意识，学院定于九月第二周开展网络安全宣传周系列活动。"},
    {"id": "N-02", "title": "关于2026年秋季学期实验室开放安排的通知", "unit": "网络空间安全学院实验中心", "date": "2026-09-02", "category": "教学通知", "summary": "本学期实验室开放时间调整为工作日 08:00-22:00，周末需提前一天预约。"},
    {"id": "N-03", "title": "关于举办第八届网络攻防竞赛的公告", "unit": "网络空间安全学院", "date": "2026-09-03", "category": "竞赛公告", "summary": "竞赛面向全校本科生，采用线上初赛与线下决赛两阶段方式进行。"},
    {"id": "N-04", "title": "关于做好2026年本科生实习工作的通知", "unit": "教务办公室", "date": "2026-09-04", "category": "教学通知", "summary": "请各专业按期完成实习组织工作，实习结束后一周内提交实习手册。"},
    {"id": "N-05", "title": "关于开展研究生学术论坛征稿的公告", "unit": "研究生工作办公室", "date": "2026-09-05", "category": "学术公告", "summary": "论坛征稿截止日期为十月十五日，录用论文将结集出版。"},
    {"id": "N-06", "title": "关于2026年国家奖学金评审结果的公示", "unit": "学生工作办公室", "date": "2026-09-06", "category": "公示公告", "summary": "现将本年度国家奖学金评审结果予以公示，公示期为五个工作日。"},
    {"id": "N-07", "title": "关于校园网核心设备升级维护的通知", "unit": "信息化建设办公室", "date": "2026-09-07", "category": "服务通知", "summary": "升级期间教学区网络将分时段中断，每段不超过三十分钟。"},
    {"id": "N-08", "title": "关于组织参加全国大学生信息安全竞赛的公告", "unit": "网络空间安全学院", "date": "2026-09-08", "category": "竞赛公告", "summary": "学院将统一组织报名与赛前培训，请有意参加的同学按时登记。"},
    {"id": "N-09", "title": "关于2026年秋季学期通识选修课补选的通知", "unit": "教务办公室", "date": "2026-09-09", "category": "教学通知", "summary": "补选通道开放三天，逾期不再受理，请同学们及时确认课表。"},
    {"id": "N-10", "title": "关于征集智能体开发实战课程优秀案例的通知", "unit": "课程教学组", "date": "2026-09-10", "category": "教学通知", "summary": "优秀案例将纳入课程资料库，供后续同学参考学习。"},
    {"id": "N-11", "title": "关于实验室安全专项检查的公告", "unit": "网络空间安全学院实验中心", "date": "2026-09-11", "category": "安全公告", "summary": "检查重点为用电安全、危化品存放与设备运行记录，请各实验室配合。"},
    {"id": "N-12", "title": "关于2026年国庆节放假安排的通知", "unit": "学院办公室", "date": "2026-09-12", "category": "行政通知", "summary": "放假期间请做好值班安排，离开工位前关闭设备电源。"},
]

PRODUCTS = [
    {"id": "P-01", "name": "高性能计算服务器", "model": "HS-7020", "price": "128000", "vendor": "启元科技"},
    {"id": "P-02", "name": "千兆接入交换机", "model": "SW-2410G", "price": "3200", "vendor": "启元科技"},
    {"id": "P-03", "name": "网络安全审计系统", "model": "AU-3300", "price": "86000", "vendor": "恒信安全"},
    {"id": "P-04", "name": "漏洞扫描设备", "model": "VS-1200", "price": "54000", "vendor": "恒信安全"},
    {"id": "P-05", "name": "数据备份存储阵列", "model": "ST-4800", "price": "152000", "vendor": "长天存储"},
    {"id": "P-06", "name": "机架式防火墙", "model": "FW-2600", "price": "47000", "vendor": "恒信安全"},
    {"id": "P-07", "name": "入侵检测探针", "model": "ID-1500", "price": "39000", "vendor": "恒信安全"},
    {"id": "P-08", "name": "终端安全管理软件", "model": "EP-900", "price": "18000", "vendor": "启元科技"},
]

PER_PAGE = 5


def notice_pages():
    """公告分页数据。第 1 页末尾与第 2 页开头刻意重复 N-06，用于演示去重。"""
    first = NOTICES[0:PER_PAGE] + [NOTICES[5]]
    second = NOTICES[5:10]
    third = NOTICES[10:12]
    return [first, second, third]


@app.route("/")
def index():
    return render_template("index.html", notice_total=len(NOTICES), product_total=len(PRODUCTS))


@app.route("/notices")
def notices():
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        abort(400)
    pages = notice_pages()
    if page < 1 or page > len(pages):
        abort(404)
    return render_template("notices.html", rows=pages[page - 1], page=page, total=len(pages))


@app.route("/notices/<nid>")
def notice_detail(nid):
    for item in NOTICES:
        if item["id"] == nid:
            return render_template("notice_detail.html", item=item)
    abort(404)


@app.route("/products")
def products():
    return render_template("products.html", rows=PRODUCTS)


@app.route("/products/<pid>")
def product_detail(pid):
    for item in PRODUCTS:
        if item["id"] == pid:
            return render_template("product_detail.html", item=item)
    abort(404)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5099, debug=False)