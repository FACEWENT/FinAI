# 🧠 FinAI · 金融研报生成 Agent

> 基于大模型 + RAG + 多源数据融合的智能金融分析助手，支持自动撰写专业研究报告并导出 PDF。

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![DashScope](https://img.shields.io/badge/LLM-Qwen--Plus-orange.svg)](https://dashscope.aliyun.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## ✨ 项目简介

**FinAI** 是一个面向金融分析场景的 AI Agent，能够围绕用户提出的"主题/股票/行业"，**自动检索本地资料、网络资讯、A股行情、数据库报表**，并由通义千问 `qwen-plus` 模型生成结构化、可下载为 PDF 的研究报告。

它不只是一个 LLM 调用包装，而是融合了 **RAG 向量检索 / 自动数据库探针 / 实时行情爬取 / PDF 解析 / 流式 SSE 输出** 等工程能力的完整 Agent 系统。

---

## 🎯 核心特性

| 能力 | 说明 |
|---|---|
| 🔍 **本地 RAG 知识库** | FAISS 向量库 + DashScope Embeddings，支持动态阈值与词法重排序，杜绝"伪相关"召回 |
| 🌐 **网络搜索** | 内置 DuckDuckGo / SearXNG 双源切换，国内可访问 |
| 🗄️ **MySQL 自动探针** | **零配置**：自动发现表结构，识别 title/text/time 列，跨表全文检索 |
| 📈 **A股实时行情** | 基于 akshare，支持股票名 → 代码自动反查（如"茅台" → 600519） |
| 📰 **股票资讯抓取** | 围绕股票主题自动聚合相关新闻 |
| 📊 **图表数据生成** | 提供历史价格/成交量数据用于前端可视化 |
| 📄 **PDF 报告导出** | 内置 STSong-Light CID 字体，**无需外部字体文件**即可输出中文 PDF |
| 🌊 **SSE 流式响应** | 边生成边吐字，提供 ChatGPT 式的对话体验 |
| 🔄 **RAG 异步刷新** | 支持后台线程触发知识库重建，带 token 鉴权 |

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI Web (web.py)                        │
│   /analyze  /analyze_sse  /research  /report_pdf  /tools     │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│             Agent 编排层 (agent.py / research_pipeline.py)   │
│   多源融合  +  反幻觉 Prompt 规则  +  流式输出               │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                       工具集 (tools.py)                      │
├──────────┬──────────┬──────────┬──────────┬─────────┬────────┤
│ local_rag│ web_search│ mysql_data│stock_snap│stock_news│chart │
│ FAISS    │ DDG/SearX │ 自动探针  │ akshare  │ akshare  │akshare│
└──────────┴──────────┴──────────┴──────────┴─────────┴────────┘
                            ▼
                ┌────────────────────────┐
                │  LLM (qwen-plus 千问)  │
                │  + reportlab → PDF    │
                └────────────────────────┘
```

---

## 📦 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **大模型**: 阿里云通义千问 (DashScope SDK，`qwen-plus`)
- **向量检索**: LangChain + FAISS + DashScope Embeddings
- **数据库**: PyMySQL
- **金融数据**: akshare (A股行情/历史)
- **PDF 处理**: pypdf (解析) + reportlab (生成)
- **资讯**: feedparser + BeautifulSoup4
- **前端**: Jinja2 模板 + 静态资源

---

## 🚀 快速开始

### 1. 克隆并安装

```bash
git clone git@github.com:FACEWENT/FinAI.git
cd FinAI
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env`：

```env
# === 大模型 (必填) ===
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === RAG 配置 ===
RAG_SCORE_THRESHOLD=0.6
RAG_RELATIVE_MULTIPLIER=1.6
RAG_MIN_HITS=1
RAG_LEXICAL_BOOST=0.2
CHUNK_SIZE=800
CHUNK_OVERLAP=120

# === 搜索引擎 ===
SEARCH_PROVIDER=duckduckgo   # 或 searxng / off
SEARXNG_URL=

# === 本地 PDF 资料目录 (可选) ===
LOCAL_PDF_DIR=./data/pdfs
MAX_PDF_FILES=5
MAX_PDF_PAGES=6
MAX_DOWNLOAD_BYTES=2000000
SUMMARY_MAX_CHARS=6000

# === MySQL (可选) ===
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_RECENT_DAYS=30
MYSQL_TOOL_MAX_TABLES=12

# === RAG 异步刷新鉴权 ===
RAG_REFRESH_TOKEN=your-secret-token
```

### 3. 构建 RAG 向量库（可选）

如果你有本地资料想要让 Agent 调用：

```bash
# 把 PDF/文本资料放到 LOCAL_PDF_DIR 指定目录
python scripts/ingest_sources.py     # 抓取外部资料
python scripts/ingest_mysql.py       # 从 MySQL 导入
python scripts/build_vector_db.py    # 构建 FAISS 索引
```

### 4. 启动服务

```bash
uvicorn app.web:app --host 0.0.0.0 --port 8000 --reload
```

访问 `http://localhost:8000` 打开网页前端，或直接调用 API。

### 5. Docker 部署

```bash
docker build -t finai .
docker run -p 8000:8000 --env-file .env finai
```

---

## 📡 API 一览

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/` | 网页前端入口 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/tools` | 列出所有可用工具 |
| `POST` | `/tools/run` | 单独调用某个工具 |
| `POST` | `/analyze` | 普通问答（同步） |
| `POST` | `/analyze_stream` | 流式问答（chunked） |
| `GET` | `/analyze_sse?question=` | **SSE 流式问答（推荐）** |
| `POST` | `/report_pdf` | 生成研究报告 PDF |
| `POST` | `/report_bundle` | 同时返回报告文本 + PDF Base64 |
| `POST` | `/research` | **完整研报**（含搜索 + PDF + 摘要 + 图表） |
| `POST` | `/research_pdf` | 完整研报直接输出 PDF |
| `POST` | `/rag_refresh` | 后台触发 RAG 重建（需 `X-Refresh-Token` 头） |
| `GET` | `/rag_refresh/status` | 查询重建状态 |

### 调用示例

```bash
# 流式问答
curl -N "http://localhost:8000/analyze_sse?question=分析贵州茅台最近走势"

# 完整研报
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"question":"半导体行业2025展望", "pdf_urls":[]}'

# 单独调用某个工具
curl -X POST http://localhost:8000/tools/run \
  -H "Content-Type: application/json" \
  -d '{"tool":"stock_snapshot","query":"600519","limit":1}'
```

---

## 🧩 工具集详解

| 工具名 | 描述 | 实现亮点 |
|---|---|---|
| `local_rag` | 本地知识库检索 | FAISS 距离 + 动态阈值 + 中文 token 重排 |
| `web_search` | 公开网页搜索 | DDG/SearXNG 双源 + URL 反代解封装 |
| `mysql_data` | 数据库报表检索 | **自动发现表结构**，无需写 SQL |
| `stock_snapshot` | A股行情快照 | 名称→代码反查 + akshare |
| `stock_news` | 股票相关资讯 | 围绕主题聚合新闻标题 |
| `stock_chart` | 价格/成交量图表数据 | 60 天历史数据 |

---

## 🗂️ 项目结构

```
FinAI/
├── app/
│   ├── web.py                  # FastAPI 入口（236行）
│   ├── agent.py                # Agent 主逻辑 + 流式（258行）
│   ├── research_pipeline.py    # 研报多源融合流水线（165行）
│   ├── tools.py                # 6 个工具的统一注册表（187行）
│   ├── rag.py                  # FAISS RAG + 重排（42行）
│   ├── mysql_client.py         # MySQL 自动探针（250行）
│   ├── stock_client.py         # akshare 行情（226行）
│   ├── search_client.py        # 网络搜索 DDG/SearXNG（91行）
│   ├── news_client.py          # 资讯抓取
│   ├── llm_client.py           # DashScope 客户端
│   ├── pdf_utils.py            # 中文 PDF 生成
│   ├── prompts.py              # Prompt 模板
│   ├── schemas.py              # Pydantic Schema
│   └── config.py               # 配置中心
├── scripts/
│   ├── ingest_sources.py       # 资料采集
│   ├── ingest_mysql.py         # MySQL 转向量
│   └── build_vector_db.py      # 构建 FAISS 索引
├── templates/                  # Jinja2 前端模板
├── static/                     # 静态资源
├── vector_store/               # FAISS 索引（自动生成）
├── data/                       # PDF 资料目录
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 💡 工程亮点

### 1. 反幻觉 Prompt 规则
工具结果**有就提，没就禁止提**：
```
仅当你确实使用了 MySQL 数据时，才可以在报告中提及"数据库/MySQL/报表数据"。
当本地资料为空时，回答中禁止出现"根据资料""资料依据"等表述。
```

### 2. RAG 双重过滤
- **动态阈值**: `max(absolute, top_score × 1.6)`，避免单一阈值失效
- **词法重排**: 用查询词命中数加 boost，提升中英混排术语相关性

### 3. MySQL 零配置探针
- 读 `information_schema` 自动发现表
- 智能识别 `text/title/time` 列
- 用 `_is_safe_identifier` 防 SQL 注入
- `lru_cache` 缓存表元数据

### 4. SDK 兼容性兜底
DashScope 返回有时是 dict、有时是对象，用 `isinstance + getattr` 双兼容（`agent.py` 第 195-224 行）。

### 5. 中文 PDF 无依赖输出
使用 `STSong-Light` 内置 CID 字体，**不需要任何外部字体文件**。

---

## 🛣️ 路线图

- [ ] 接入更多金融数据源（港股、美股、加密货币）
- [ ] 支持多轮对话（当前为单轮 Q&A）
- [ ] Function Calling 重构（让 LLM 自主选择工具）
- [ ] 加入研报模板系统（行业研究 / 公司深度 / 量化策略）
- [ ] 前端用 React/Next 重写
- [ ] WebSocket 双向通信

---

## 📄 许可证

[MIT License](LICENSE)

---

## 🙏 致谢

- [通义千问 DashScope](https://dashscope.aliyun.com/) - 提供大模型能力
- [akshare](https://github.com/akfamily/akshare) - 开源金融数据接口
- [LangChain](https://github.com/langchain-ai/langchain) - RAG 框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

---

> **Author**: [@FACEWENT](https://github.com/FACEWENT)
> 欢迎 Issue / PR / Star ⭐
