# Zemax Agent — 光学工程工作台

面向光学工程全生命周期的 AI 原生工作平台。以项目为核心载体，统一管理设计数据、分析结果、版本记录和知识资产，使 AI 能够深度参与光学研发过程。

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **ui** | Tauri 2.x + React 19.x + TypeScript | 桌面应用壳，工程工作台多面板界面 |
| **core** | Python 3.12+ | 核心业务逻辑（Agent / 项目管理 / 任务调度 / 版本管理） |
| **tools** | Pydantic v2 | 标准化工具接口，AI 通过 Tool Interface 调用 Zemax |
| **zos** | Python.NET → ZOS-API | Zemax OpticStudio 自动化控制 |
| **llm** | LangGraph + LangChain | Agent 状态图编排与 Human-in-the-loop |
| **storage** | SQLite + Qdrant | 项目元数据 / 知识向量检索 |
| **ipc** | Tauri sidecar stdin/stdout JSON | 前后端进程间通信 |

## 系统架构

```
┌────────────────────────────────────────────────────┐
│           Tauri Desktop (React + TS)               │
│  Project Explorer │ Design │ Analysis │ AI Chat   │
└──────────────────────┬─────────────────────────────┘
                       │ Tauri IPC (sidecar JSON)
┌──────────────────────┴─────────────────────────────┐
│              Python Core Layer                     │
│  AgentOrchestrator → Tool Registry → ZOS Dispatcher│
│  Project Manager │ Version Manager │ Knowledge Base│
└──────────────────────┬─────────────────────────────┘
                       │ Python.NET / CLR
┌──────────────────────┴─────────────────────────────┐
│            Zemax OpticStudio (ZOS-API)             │
└────────────────────────────────────────────────────┘
```

## 快速入门

### 环境要求

- Windows 10/11
- Python 3.10+
- Zemax OpticStudio (licensed)
- Node.js 20+ (前端开发)
- Rust (Tauri 编译)

### 安装

```bash
# 克隆仓库
git clone <repo-url>
cd zemax-agent

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install

# 安装前端依赖
cd frontend
npm install
```

### 配置

复制并编辑配置文件：

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入 LLM API Key 和 Zemax 连接参数
```

### 运行

```bash
# 开发模式 — 启动 Python 核心
python -m zemax_agent.core

# 开发模式 — 启动 Tauri 前端
cd frontend
npm run tauri dev

# 生产构建
cd frontend
npm run tauri build
```

### 运行测试

```bash
# 后端测试
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=zemax_agent --cov-report=html
```

## 项目目录结构

```
zemax-agent/
├── src/zemax_agent/
│   ├── core/           # AgentOrchestrator, 工作流引擎, 任务调度
│   ├── tools/          # Pydantic Tool Registry, 标准化工具接口
│   ├── zos/            # ZOS Dispatcher, ZOS-API 封装层
│   ├── knowledge/      # 知识库, RAG Pipeline, 向量检索
│   └── llm/            # LLM Provider (多模型支持)
├── frontend/           # Tauri + React + TypeScript 前端
├── tests/              # 测试
├── config.yaml         # 配置文件
├── pyproject.toml      # Python 项目配置
└── README.md
```

## License

MIT
