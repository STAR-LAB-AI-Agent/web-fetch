# AI 网页信息采集

基于 **Playwright Python** 的自然语言智能体应用：从指定网页采集用户要求的字段，整理成 **JSON** 等结构化结果。

> 《智能体开发实战》课程实验任务书 · 第 22 题 · **初版 v1 骨架**
>
> 本版本（v1）的目标是先打通一条端到端核心闭环：**从表格页采集用户指定的字段并导出 JSON**。
> 卡片列表页、详情页、CSV/Excel 导出、多网页采集与去重将在后续迭代中加入（见文末「迭代路线」）。

## 用户场景

用户用一句自然语言指定「采哪个页面、要哪些字段」：

- 「采集公告列表的标题、发布时间和链接」
- 「采集公告的编号、标题和发布单位」
- 「只要公告的标题」

## 系统结构

```
用户自然语言 → WebAgent(agent.py) → router(字段/页面解析) → extract(Playwright 采集) → export(JSON)
                                   ↑ 离线规则解析 fallback（无大模型也能完整运行）
```

| 模块 | 职责 |
|------|------|
| `mock_site/app.py` | 本地模拟目标网站：公告列表（表格结构），作为可复现的采集对象 |
| `web_agent/extract.py` | 采集核心：按表头解析字段，输出结构化行记录 |
| `web_agent/router.py` | 自然语言 → 采集计划（目标页面、字段） |
| `web_agent/export.py` | 导出 JSON |
| `web_agent/agent.py` | 编排工具调用，可选接入在线模型解析 |
| `web_agent/cli.py` | 子命令 CLI，统一输出 JSON |
| `SKILL.md` | Skill 说明（使用场景 / 参数 / 步骤 / 示例） |

## 安装

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium                          # 首次运行需下载浏览器内核
```

> 开发/验证环境：Windows + Python 3.13.15。代码仅使用 Python 3.10+ 语法；请务必使用 venv 独立环境。

## 运行

### 1. 启动本地模拟目标网站

```bash
python mock_site/app.py          # 默认 http://127.0.0.1:5099
```

### 2. 自然语言端到端

```bash
python -m web_agent.cli agent --base http://127.0.0.1:5099 \
  --text "采集公告列表的标题、发布时间和链接" --out notices.json
```

### 3. 单步 CLI（确定性，便于独立测试）

```bash
# 按字段采集公告列表，导出 JSON
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices \
  --fields 标题,发布时间,链接 --out notices.json

# 不指定字段时，采集该表格的全部列
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices
```

### 4. 配置在线模型解析（可选）

复制 `.env.example` 为 `.env` 并填入兼容 OpenAI 接口的服务；**不配也能用离线规则解析完成全部基础功能**，模型调用失败时会自动回退。

> 真实 API Key 请勿提交到 Git：`.env` 已在 `.gitignore` 中排除，仓库只保留脱敏的 `.env.example`。

## 支持的页面结构与字段

| 结构 | 说明 | 行选择器 |
|------|------|----------|
| `table` | 标准表格页，列名自动取 `thead` 中的表头 | `table tbody tr`（可用 `--row-selector` 指定） |

用户说法会按同义词表匹配到页面上的实际列名，例如「日期 → 发布时间」「详情/地址/网址 → 链接」；请求了页面上不存在的字段时，结果中该字段为空并在 `missing_fields` 中列出，不会静默丢失。

## 测试

```bash
pytest -v
```

| 用例文件 | 覆盖内容 | 是否需要浏览器 |
|----------|----------|----------------|
| `tests/test_router.py` | 自然语言解析：目标页面、字段 | 否 |
| `tests/test_extract.py` | 字段匹配与表格解析 | 否 |
| `tests/test_export.py` | JSON 导出与异常处理 | 否 |
| `tests/test_mock_site.py` | 模拟站点表格页行为 | 否 |
| `tests/test_agent_integration.py` | 采集到导出的端到端链路 | 是（未装内核时自动跳过） |

> 测试在 `tests/conftest.py` 中统一移除 `OPENAI_API_KEY`，固定走离线规则解析，不依赖外部模型、结果可复现。

## 开源选型说明

任务书为本题目给出的参考开源项目为 **browser-use 与 Playwright**。本实现选择 Playwright 作为底层采集引擎：它不依赖在线模型即可完成确定性采集，便于离线演示与自动化测试；browser-use 的定位是把浏览器操作交给大模型决策，与本项目「确定性优先」的设计目标不同，因此仅作为设计思路参考，未引入依赖。

## 开源依赖与许可证

| 项目 | 版本 | 许可证 | 用途 | 来源 |
|------|------|--------|------|------|
| Playwright | >=1.40 | Apache-2.0 | 浏览器自动化与页面采集（核心能力） | https://playwright.dev/python/ |
| Flask | >=3.0 | BSD-3-Clause | 本地模拟目标网站（仅演示/测试对象） | https://flask.palletsprojects.com/ |

## 安全与低 Token 措施

- **最小权限**：只访问 `--base` 指定的站点，不外联其他域名；不自动跟随站外链接。
- **低 Token**：采集在浏览器侧用脚本完成，**不把整页 HTML 交给模型**；只有用户在离线规则下无法匹配的字段，才会请求模型解析一次计划。
- **敏感信息**：`--fields` 与输出文件由用户显式指定；导出文件若包含个人信息，由使用者自行保管。
- **日志**：仅记录访问的 URL 与采集条数，不记录 API Key；`.env` 已排除在版本库外。
- **可复现**：采集过程不依赖随机等待，同一页面多次采集结果一致。

## 迭代路线（后续版本将覆盖）

- 支持卡片式列表页与详情页（`list` / `item` 两种结构）。
- 增加 CSV / Excel 导出格式。
- 支持多网页采集与结果去重（任务书可选功能）。
- 补齐边界与异常测试用例。

## 已知问题

- 仅支持表格类列表页；卡片式列表与详情页尚未支持。
- 导出格式仅 JSON。
- 不处理前端异步渲染与无限滚动，`domcontentloaded` 之后仅做确定性读取。
- 模拟站点数据存内存，重启清空（仅演示/测试用）。