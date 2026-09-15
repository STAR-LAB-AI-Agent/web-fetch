---
name: web-fetch
description: 通过自然语言从指定网页采集用户要求的字段，整理成 JSON/CSV/Excel 等结构化结果；基于 Playwright Python 实现确定性页面采集，支持表格与卡片列表、详情页单条记录，以及多网页结果去重。
version: 0.1.0
license: MIT
---

# SKILL：AI 网页信息采集

## 使用场景

当用户需要「从某个网页上把指定字段取下来，并整理成结构化数据」时调用本 Skill，例如：
采集公告列表的标题与发布时间、采集设备列表的型号与价格、采集详情页的正文与附件链接，
并按 JSON / CSV / Excel 之一输出。

## 参数与调用方式

- 入口：`python -m web_agent.cli agent --base <站点URL> --text "<自然语言>" [--out <文件>]`
- 确定性调用：`python -m web_agent.cli collect --base <站点URL> --path <路径> --fields <字段,...> --format <json|csv|xlsx> --out <文件>`
- 也可直接调用 Python：`WebAgent(base_url=...).run("自然语言需求")`
- 常用可选参数：`--pages 1,2|all`（多页）、`--dedup-by <字段>`（去重）、`--kind auto|table|list|item`、
  `--row-selector <选择器>`、`--headed`（显示浏览器）。

## 工具清单（智能体可调用的能力）

| 工具 | 说明 | 关键参数 |
|------|------|----------|
| `collect_page` | 采集单个页面，按用户要求的字段输出结构化记录 | `path` `fields` `kind` `page` |
| `collect_pages` | 多网页采集并合并去重（可选功能） | `path` `pages` `fields` `dedup_by` |
| `export_result` | 把记录导出成 JSON / CSV / Excel | `records` `fmt` `path` |

## 调用步骤

1. 解析自然语言 → 得到采集计划：目标路径、字段列表、页数、导出格式、是否去重。
2. 打开目标页面，识别结构（表格 / 卡片列表 / 详情页）。
3. 按字段抽取为行记录；页面中不存在的字段置空并在 `missing_fields` 中列出。
4. 多页采集时按指定字段去重，保留首次出现的记录。
5. 按指定格式写出文件，并返回条数、重复条数与输出路径。

## 结果格式

统一返回 JSON dict：`{"ok": bool, "action": "collect", "input": str, "plan": {...},
"count": int, "duplicates_removed": int, "missing_fields": [...], "records": [...], "export": {...}}`。

## 示例

### 示例 1：自然语言采集并导出 Excel

```bash
python -m web_agent.cli agent --base http://127.0.0.1:5099 \
  --text "把前两页公告的标题、发布时间和链接导出成 Excel" --out notices.xlsx
```

预期：`plan.path = /notices`、`plan.fields = ["标题","发布时间","链接"]`、
`plan.pages = [1,2]`、`plan.format = "xlsx"`，输出 11 条记录。

### 示例 2：多网页采集 + 去重

```bash
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices \
  --pages all --dedup-by 编号 --format xlsx --out all_notices.xlsx
```

预期：采集 3 页共 13 条，按编号去重后 12 条，`duplicates_removed = 1`。

### 示例 3：采集详情页的正文与附件链接

```bash
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices/N-01 \
  --kind item --fields 标题,发布单位,发布时间,正文,链接
```

## 安全与最小权限

- 只访问 `--base` 指定的站点，不外联其他域名。
- 不返回整页 HTML：采集在浏览器侧完成，模型只参与字段与页面解析。
- 密钥通过环境变量提供，日志不记录密钥；`.env` 已排除在版本库外。
- 输出文件路径由用户显式指定，避免覆盖无关文件。