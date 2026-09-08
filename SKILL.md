---
name: ai-web-operation
description: 通过自然语言查询本地模拟业务网站的可预约时段（初版 v1）。预约/填报将在后续迭代提供。
version: 0.1.0
license: MIT
---

# SKILL：AI 网页业务操作（初版 v1）

## 使用场景

当用户需要对（教师提供的）本地模拟业务网站查询某日可预约时段时使用。
初版仅完成「查询」意图的端到端闭环；收到预约/填报类指令时返回“后续迭代支持”提示。

## 参数与调用方式

- 入口：`python -m web_agent.cli agent --base <站点URL> --text "<自然语言>"`
- 单步：`python -m web_agent.cli query --base <站点URL> --date YYYY-MM-DD`
- 也可直接调用：`WebAgent(base_url=...).execute("查询明天可预约时段")`

## 工具

| 工具 | 说明 | 关键参数 |
|------|------|----------|
| `query_slot` | 查询某日可预约时段 | `date`（YYYY-MM-DD，可省略） |

## 结果格式

统一 JSON dict：`{"ok": true, "url": ..., "date": ..., "slots": [{"time","used","status"}], "plan": {...}}`。
预约/填报等暂未支持意图返回 `{"ok": false, "error": "将在后续迭代版本提供"}`。

## 示例

```bash
python -m web_agent.cli agent --base http://127.0.0.1:5099 --text "查询明天可预约时段"
```

返回 `slots` 列表（如 `09:00/10:30/14:00/16:00` 及其可约状态）。

## 安全与最小权限

- 仅访问 `--base` 指定的站点，默认 headless 运行，不外联其他域名。
- 暂不包含任何提交类操作，因此初版不涉及网页提交类风险操作。