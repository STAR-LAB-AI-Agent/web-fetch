# AI 网页信息采集

基于 **Playwright Python** 的自然语言智能体应用：从指定网页采集用户要求的字段，整理成 **JSON / CSV / Excel** 等结构化结果。

> 《智能体开发实战》课程实验任务书 · 第 22 题 · 基础任务 + 可选功能（多网页结果去重）

## 用户场景

用户用一句自然语言指定「采哪个页面、要哪些字段、导成什么格式」：

- 「把前两页公告的标题、发布时间和链接导出成 Excel」
- 「采集设备列表里所有设备的名称、型号和价格，输出 CSV」
- 「采集这份公告详情页的标题、发布单位、正文和附件链接」
- 「采集全部公告的编号和标题并去重」

## 系统结构

```
用户自然语言 → WebAgent(agent.py) → router(字段/页面解析) → extract(Playwright 采集)
                                   → dedup(多网页去重) → export(JSON / CSV / Excel)
                                   ↑ 离线规则解析 fallback（无大模型也能完整运行）
```

| 模块 | 职责 |
|------|------|
| `mock_site/app.py` | 本地模拟目标网站：公告列表（表格）、设备列表（卡片）及各自详情页，作为可复现的采集对象 |
| `web_agent/extract.py` | 采集核心：按表头/卡片标签解析字段，输出结构化行记录 |
| `web_agent/router.py` | 自然语言 → 采集计划（目标页面、字段、页数、导出格式、去重字段） |
| `web_agent/dedup.py` | 多网页结果去重（可选功能） |
| `web_agent/export.py` | 导出 JSON / CSV / Excel |
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
  --text "把前两页公告的标题、发布时间和链接导出成 Excel" --out notices.xlsx
```

### 3. 单步 CLI（确定性，便于独立测试）

```bash
# 列表页：按字段采集，导出 CSV
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices \
  --fields 标题,发布时间,链接 --format csv --out notices.csv

# 多网页采集 + 按编号去重（可选功能）
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices \
  --pages all --dedup-by 编号 --format xlsx --out all_notices.xlsx

# 卡片式列表页
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /products \
  --fields 名称,型号,价格,供应商 --format csv

# 详情页（单条记录）
python -m web_agent.cli collect --base http://127.0.0.1:5099 --path /notices/N-01 \
  --kind item --fields 标题,发布单位,发布时间,正文,链接
```

### 4. 配置在线模型解析（可选）

复制 `.env.example` 为 `.env` 并填入兼容 OpenAI 接口的服务；**不配也能用离线规则解析完成全部基础功能**，模型调用失败时会自动回退。

> 真实 API Key 请勿提交到 Git：`.env` 已在 `.gitignore` 中排除，仓库只保留脱敏的 `.env.example`。

## 支持的页面结构与字段

| 结构 | 说明 | 行选择器 |
|------|------|----------|
| `table` | 标准表格页，列名自动取 `thead` 中的表头 | `table tbody tr` |
| `list` | 卡片/条目列表页，块内按「标签：值」解析 | `.card` / `article` / `li`（自动探测，可用 `--row-selector` 指定） |
| `item` | 详情页，采集单条记录 | —— |

字段名支持常见同义说法，例如「价格 → 参考价」「日期 → 发布时间」「详情/地址/网址 → 链接」；请求了页面上不存在的字段时，结果中该字段为空并在 `missing_fields` 中列出，不会静默丢失。

## 测试

```bash
pytest -v
```

| 用例文件 | 覆盖内容 | 是否需要浏览器 |
|----------|----------|----------------|
| `tests/test_router.py` | 自然语言解析：目标页面、字段、页数、格式、去重 | 否 |
| `tests/test_extract.py` | 字段匹配与表格/卡片/详情页解析 | 否 |
| `tests/test_export.py` | JSON / CSV / Excel 导出与异常处理 | 否 |
| `tests/test_dedup.py` | 多网页结果去重 | 否 |
| `tests/test_mock_site.py` | 模拟站点分页、详情、404 等行为 | 否 |
| `tests/test_agent_integration.py` | 采集到导出的端到端链路 | 是（未装内核时自动跳过） |

> 测试在 `tests/conftest.py` 中统一移除 `OPENAI_API_KEY`，固定走离线规则解析，不依赖外部模型、结果可复现。

## 开源选型说明

任务书为本题目给出的参考开源项目为 **browser-use 与 Playwright**。本实现选择 Playwright 作为底层采集引擎：它不依赖在线模型即可完成确定性采集，便于离线演示与自动化测试；browser-use 的定位是把浏览器操作交给大模型决策，与本项目“确定性优先”的设计目标不同，因此仅作为设计思路参考，未引入依赖。

## 开源依赖与许可证

| 项目 | 版本（实测） | 许可证 | 用途 | 来源 |
|------|------|--------|------|------|
| Playwright | >=1.40（1.62.0） | Apache-2.0 | 浏览器自动化与页面采集（核心能力） | https://playwright.dev/python/ |
| openpyxl | >=3.1 | MIT | 采集结果导出 Excel | https://openpyxl.readthedocs.io/ |
| Flask | >=3.0（3.1.3） | BSD-3-Clause | 本地模拟目标网站（仅演示/测试对象） | https://flask.palletsprojects.com/ |

## 安全与低 Token 措施

- **最小权限**：只访问 `--base` 指定的站点，不外联其他域名；不自动跟随站外链接。
- **低 Token**：采集在浏览器侧用脚本完成，**不把整页 HTML 交给模型**；只有用户在离线规则下无法匹配的字段，才会请求模型解析一次计划。实测公告列表页整页 HTML 约 1.9 KB 字符，而参与模型交互的只有字段名清单（约 30 字）。
- **敏感信息**：`--fields` 与输出文件由用户显式指定；导出文件若包含个人信息，由使用者自行保管。
- **写文件确认**：导出目标已存在同名文件时，先询问「该文件已存在，是否覆盖？」，确认后才写入；非交互环境（管道、自动化脚本）默认不覆盖，可用 `--force` 跳过询问。
- **日志**：仅记录访问的 URL 与采集条数，不记录 API Key；`.env` 已排除在版本库外。
- **可复现**：采集过程不依赖随机等待，同一页面多次采集结果一致。

## 已知问题

- 卡片式列表页依赖「标签：值」的书写形式才能解析出字段名，若目标站点没有标签行，需要用 `--row-selector` 配合自定义选择器。
- 若目标页面内容由前端异步渲染，`domcontentloaded` 之后可能仍有延迟；当前仅对表格/卡片做确定性读取，未做无限滚动加载。
- 模拟站点数据存内存，重启清空（仅演示/测试用）。