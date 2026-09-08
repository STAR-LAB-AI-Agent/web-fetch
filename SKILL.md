---
name: web-fetch
description: 通过自然语言从指定网页采集用户要求的字段，整理成 JSON 结构化结果；基于 Playwright Python 实现确定性页面采集，初版覆盖表格类列表页。
version: 0.1.0
license: MIT
---

# SKILL：AI 网页信息采集（v1 骨架）

## 使用场景

当用户需要「从某个网页上把指定字段取下来，并整理成结构化数据」时调用本 Skill，例如：
采集公告列表的标题与发布时间、采集公告的编号与发布单位，并以 JSON 输出。

> 本版只覆盖表格类列表页；卡片列表页、详情页与 CSV/Excel 输出将在后续迭代中加入。

## 参数与调用方式

- 入口：`python -m web_agent.cli agent --base <站点URL> --text "<自然语言>" [--out <文件>]`
- 确定性调用：`python -m web_agent.cli collect --base <站点URL> --path <路径> --fields <字段,...> [--out <文件>]`
- 也可直接调用 Python：`WebAgent(base_url=...).run("自然语言需求")`
- 常用可选参数：`--row-selector <选择器>`（自定义表格行选择器）、`--headed`（显示浏览器）。

## 工具清单（智能体可调用的能力）

| 工具 | 说明 | 关键参数 |
|------|------|----------|
| `collect_page` | 采集单个页面，按用户要求的字段输出结构化记录 | `path` `fields` `row_selector` |
| `export_result` | 把记录导出成 JSON | `records` `fmt` `path` |

## 调用步骤

1. 解析自然语言 → 得到采集计划：目标路径与字段列表。
2. 打开目标页面，确认是表格结构（表头 + 数据行）。
3. 按字段抽取为行记录；页面中不存在的字段置空并在 `missing_fields` 中列出。
4. 写出 JSON 文件，并返回条数与输出路径。

## 结果格式

统一返回 JSON dict：`{"ok": bool, "action": "collect", "input": str, "plan": {...},
"count": int, "missing_fields": [...], "records": [...], "export": {...}}`。

## 示例

### 示例 1：自然语言采集并导出 JSON

```bash
python -m web_agent.cli agent --base http://127.0.0.1:5099 \
  --text "采集公告列表的标题、发布时间和链接" --out notices.json
```

预期：`plan.path = /notices`、`plan.fields = ["标题","发布时间","链接"]`，输出 12 条记录。

### 示例 2：确定性单步采集

```bash
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices \
  --fields 编号,标题,发布单位 --out notices.json
```

### 示例 3：不指定字段时采集全部列

```bash
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices
```

## 安全与最小权限

- 只访问 `--base` 指定的站点，不外联其他域名。
- 不返回整页 HTML：采集在浏览器侧完成，模型只参与字段与页面解析。
- 密钥通过环境变量提供，日志不记录密钥；`.env` 已排除在版本库外。
- 输出文件路径由用户显式指定，避免覆盖无关文件。