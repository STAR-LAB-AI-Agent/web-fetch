"""本地模拟业务网站（服务预约系统）——初版（v1）。

初版只提供「查询可预约时段」页面；预约(/book)、填报(/report) 及对应
业务逻辑将在后续迭代版本中加入。数据存内存，重启即清空（仅演示/测试用）。
"""
from __future__ import annotations

from datetime import date, timedelta

from flask import Flask, render_template, request

app = Flask(__name__)

SLOTS = ["09:00", "10:30", "14:00", "16:00"]
CAPACITY = 3
# 内存数据：{"YYYY-MM-DD": {"09:00": 已约数, ...}}
_store: dict[str, dict[str, int]] = {}


def _slots_for(day: str) -> list[dict]:
    used = _store.setdefault(day, {s: 0 for s in SLOTS})
    rows = []
    for s in SLOTS:
        remain = max(0, CAPACITY - used.get(s, 0))
        rows.append({"time": s, "used": used.get(s, 0), "status": f"{remain} 可约" if remain else "已约满"})
    return rows


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/query")
def query():
    day = request.args.get("date") or (date.today() + timedelta(days=1)).isoformat()
    return render_template("query.html", date=day, slots=_slots_for(day))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5099, debug=False)