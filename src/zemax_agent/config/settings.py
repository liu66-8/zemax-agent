from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ZemaxConfig(BaseModel):
    connection_mode: str = "standalone"
    connection_timeout: float = 30.0
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 3


class LLMConfig(BaseModel):
    provider: str = "openai"
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.1
    request_timeout: float = 60.0
    max_retries: int = 3


class OptimizationConfig(BaseModel):
    max_iterations: int = 100
    convergence_threshold: float = 1e-6
    auto_hammer: bool = False


class ToleranceConfig(BaseModel):
    default_sample_count: int = 500


class AppConfig(BaseModel):
    zemax: ZemaxConfig = Field(default_factory=ZemaxConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)
    tolerance: ToleranceConfig = Field(default_factory=ToleranceConfig)
    workspace_dir: str = "./workspace"
    checkpoint_dir: str = "./checkpoints"
    log_level: str = "INFO"
    log_file: str = "./logs/zemax_agent.log"


_CONFIG_SECTIONS: dict[str, type[BaseModel]] = {
    "zemax": ZemaxConfig,
    "llm": LLMConfig,
    "optimization": OptimizationConfig,
    "tolerance": ToleranceConfig,
}

_TOP_LEVEL_FIELDS = {
    "workspace_dir",
    "checkpoint_dir",
    "log_level",
    "log_file",
}


def _apply_env_overrides(config: AppConfig) -> AppConfig:
    data: dict[str, Any] = {}
    section_overrides: dict[str, dict[str, Any]] = {}

    for key, value in os.environ.items():
        if not key.startswith("ZEMAX_AGENT_"):
            continue
        suffix = key[len("ZEMAX_AGENT_"):]
        if "__" in suffix:
            section_name, field_name = suffix.split("__", 1)
            section_lower = section_name.lower()
            field_lower = field_name.lower()
            if section_lower in _CONFIG_SECTIONS:
                section_overrides.setdefault(section_lower, {})[field_lower] = value
        else:
            field_lower = suffix.lower()
            if field_lower in _TOP_LEVEL_FIELDS:
                data[field_lower] = value

    if data:
        top_validated = AppConfig.model_validate(data)
        for field_name in data:
            setattr(config, field_name, getattr(top_validated, field_name))

    for section_name, fields in section_overrides.items():
        model_cls = _CONFIG_SECTIONS.get(section_name)
        if model_cls is None:
            continue
        section_obj = getattr(config, section_name)
        merged = section_obj.model_dump()
        merged.update(fields)
        updated_section = model_cls.model_validate(merged)
        setattr(config, section_name, updated_section)

    return config


def _config_to_dict(config: AppConfig) -> dict[str, Any]:
    result: dict[str, Any] = config.model_dump()
    return result


class ConfigManager:
    _instance: ConfigManager | None = None
    _config: AppConfig | None = None

    def __init__(self, config_path: str = "config.yaml") -> None:
        self._config_path = Path(config_path)

    @classmethod
    def _get_instance(cls, config_path: str = "config.yaml") -> ConfigManager:
        if cls._instance is None:
            cls._instance = cls(config_path=config_path)
        return cls._instance

    def load(self) -> AppConfig:
        if self._config_path.exists():
            raw = yaml.safe_load(self._config_path.read_text(encoding="utf-8")) or {}
        else:
            raw = {}
            self._create_default_config()

        config = AppConfig.model_validate(raw)
        config = _apply_env_overrides(config)
        self._config = config
        ConfigManager._config = config
        return config

    def save(self) -> None:
        if self._config is None:
            self.load()
        assert self._config is not None
        config_dict = _config_to_dict(self._config)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            yaml.dump(config_dict, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )

    def get(self) -> AppConfig:
        if self._config is None:
            self.load()
        assert self._config is not None
        return self._config

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        cls._config = None

    def _create_default_config(self) -> None:
        default = AppConfig()
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            f.write(_DEFAULT_CONFIG_TEMPLATE)
        self._config = default
        ConfigManager._config = default


_DEFAULT_CONFIG_TEMPLATE = """\
# =============================================================================
# Zemax-Agent 默认配置文件
# 所有配置项均设有默认值，可按需修改
# 环境变量覆盖规则：ZEMAX_AGENT_<SECTION>__<KEY>（优先级最高）
# =============================================================================

# -----------------------------------------------------------------------------
# Zemax OpticStudio 连接配置
# -----------------------------------------------------------------------------
zemax:
  # 连接模式: standalone（独立模式）| extension（扩展模式）
  connection_mode: standalone
  # 连接超时时间（秒）
  connection_timeout: 30.0
  # 断开后是否自动重连
  auto_reconnect: true
  # 最大重连尝试次数
  max_reconnect_attempts: 3

# -----------------------------------------------------------------------------
# 大语言模型 (LLM) 配置
# -----------------------------------------------------------------------------
llm:
  # LLM 服务提供商: openai | azure | local
  provider: openai
  # API 密钥（建议通过环境变量 ZEMAX_AGENT_LLM__API_KEY 设置）
  api_key: ""
  # API 基础地址
  api_base: https://api.openai.com/v1
  # 模型名称
  model: gpt-4
  # 最大生成 token 数
  max_tokens: 4096
  # 生成温度（越低越确定性）
  temperature: 0.1
  # 请求超时时间（秒）
  request_timeout: 60.0
  # 最大重试次数
  max_retries: 3

# -----------------------------------------------------------------------------
# 光学系统优化配置
# -----------------------------------------------------------------------------
optimization:
  # 最大迭代次数
  max_iterations: 100
  # 收敛阈值
  convergence_threshold: 1.0e-06
  # 是否在优化后自动执行 Hammer 优化
  auto_hammer: false

# -----------------------------------------------------------------------------
# 公差分析配置
# -----------------------------------------------------------------------------
tolerance:
  # 默认蒙特卡洛采样数
  default_sample_count: 500

# -----------------------------------------------------------------------------
# 通用配置
# -----------------------------------------------------------------------------
# 工作目录
workspace_dir: ./workspace
# 检查点保存目录
checkpoint_dir: ./checkpoints
# 日志级别: DEBUG | INFO | WARNING | ERROR | CRITICAL
log_level: INFO
# 日志文件路径
log_file: ./logs/zemax_agent.log
"""
