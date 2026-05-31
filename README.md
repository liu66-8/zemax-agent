# Zemax-Agent 智能光学设计系统

基于 LLM 大语言模型驱动的多智能体光学设计系统，通过 Zemax ZOS-API 实现自动化光学设计工作流、分析与优化。

## 核心功能

系统包含六大核心模块：

| 模块 | 说明 |
|------|------|
| **API 封装层** (`api/`) | 封装 Zemax OpticStudio 的 ZOS-API，管理连接生命周期、命令执行与数据获取 |
| **Agent 决策引擎** (`agent/`) | 基于 LLM 的多智能体编排核心，管理 Agent 行为、工具选择与迭代设计工作流 |
| **光学计算与诊断** (`optics/`) | 实现光学性能指标计算、像差分析、MTF/PSF 计算与系统级光学诊断 |
| **知识约束** (`knowledge/`) | 编码光学设计原理、约束条件与最佳实践，为 Agent 决策提供结构化知识支持 |
| **报告生成** (`report/`) | 基于 Jinja2 模板生成结构化光学设计报告，包含性能总结、分析图表与设计文档 |
| **会话管理** (`session/`) | 管理设计会话、检查点持久化、状态恢复与长运行工作流跟踪 |

## 系统架构

```
┌─────────────────────────────────────┐
│           CLI Entry Point           │
├─────────────────────────────────────┤
│        Agent 决策引擎 (agent/)       │  ← LLM 推理与任务编排
├─────────────────────────────────────┤
│   API 封装层 (api/)  │ 工具库 (tools/)│ ← 与 Zemax 交互
├─────────────────────────────────────┤
│  光学计算 (optics/) │ 知识库 (knowledge/)│ ← 领域专用层
├─────────────────────────────────────┤
│   会话管理 (session/) │ 配置 (config/)  │ ← 基础设施层
└─────────────────────────────────────┘
```

四层架构设计：

1. **接入层** — CLI 入口与外部接口
2. **决策层** — LLM 驱动的 Agent 智能体引擎
3. **领域层** — 光学计算、分析诊断与专业知识库
4. **基础层** — 配置管理、会话持久化与状态恢复

## 安装指南

### 环境要求

- **Python** >= 3.10
- **Zemax OpticStudio** (提供 ZOS-API 支持)
- **LLM API Key** (如 OpenAI API Key)

### 从源码安装

```bash
git clone <repository-url>
cd zemax-agent
pip install -e .
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

## 快速开始

```bash
# 启动 zemax-agent
zemax-agent
```

在 Python 中使用：

```python
from zemax_agent import __version__

print(f"Zemax-Agent version: {__version__}")
```

## 依赖要求

### 核心依赖

- pydantic >= 2.0 — 配置与数据校验
- pyyaml >= 6.0 — YAML 配置文件解析
- numpy >= 1.24 — 数值计算
- pandas >= 2.0 — 数据处理与分析
- matplotlib >= 3.7 — 图表可视化
- openai >= 1.0 — LLM 客户端
- jinja2 >= 3.1 — 报告模板引擎

### 开发依赖

- pytest >= 7.0
- pytest-asyncio >= 0.21
- pytest-cov >= 4.0
- ruff >= 0.1
- mypy >= 1.0

### 外部依赖

- Zemax OpticStudio（支持 ZOS-API）
- LLM API Key（如 OpenAI）

## 项目结构

```
zemax-agent/
├── src/zemax_agent/
│   ├── __init__.py          # 包入口，版本号
│   ├── cli.py               # CLI 命令行入口
│   ├── config/              # 配置管理模块
│   ├── api/                 # ZOS-API 封装层
│   ├── tools/               # 工具函数库
│   ├── knowledge/           # 光学知识约束
│   ├── agent/               # Agent 决策引擎
│   ├── optics/              # 光学计算与诊断
│   ├── report/              # 报告生成模块
│   ├── session/             # 会话与状态管理
│   └── llm/                 # LLM 客户端
├── tests/
│   ├── conftest.py          # Pytest 配置文件
│   ├── test_config/         # 配置模块测试
│   ├── test_api/            # API 封装层测试
│   ├── test_tools/          # 工具函数测试
│   ├── test_knowledge/      # 知识约束测试
│   ├── test_agent/          # 决策引擎测试
│   ├── test_optics/         # 光学计算测试
│   ├── test_report/         # 报告生成测试
│   └── test_session/        # 会话管理测试
├── pyproject.toml           # 项目配置与依赖
├── .pre-commit-config.yaml  # Pre-commit hooks
├── .gitignore               # Git 忽略规则
└── README.md                # 本文件
```

## 许可证

待定。
