from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, model_validator


class ZOSConfig(BaseModel):
    connection_mode: str = "standalone"
    connection_timeout: float = 30.0
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 3
    task_queue_max_size: int = 100
    heartbeat_interval: float = 5.0


class LLMConfig(BaseModel):
    provider: str = "openai"
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.1
    request_timeout: float = 60.0
    max_retries: int = 3
    context_window_size: int = 128000
    max_context_messages: int = 20


class StorageConfig(BaseModel):
    db_path: str = "./zemax_agent.db"
    qdrant_url: str = "http://localhost:6333"
    qdrant_prefer_grpc: bool = False
    embedder_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedder_device: str = "cpu"


class ProjectConfig(BaseModel):
    workspace_dir: str = "./workspace"
    template_dir: str = "./templates"


class OptimizationConfig(BaseModel):
    max_iterations: int = 100
    convergence_threshold: float = 1.0e-06
    auto_hammer: bool = False
    stagnation_threshold: int = 5
    stagnation_change_rate: float = 1.0e-04


class ToleranceConfig(BaseModel):
    default_sample_count: int = 500


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "./logs/zemax_agent.log"
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class AppConfig(BaseModel):
    zos: ZOSConfig = Field(default_factory=ZOSConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)
    tolerance: ToleranceConfig = Field(default_factory=ToleranceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    workspace_dir: str = "./workspace"
    checkpoint_dir: str = "./checkpoints"

    def model_post_init(self, __context: Any) -> None:
        self._apply_top_level_env_overrides()

    def _apply_top_level_env_overrides(self) -> None:
        prefix = "ZEMAX_AGENT_"
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            config_key = key[len(prefix):].lower()
            if "__" not in config_key and hasattr(self, config_key):
                setattr(self, config_key, self._coerce_env_value(value))

    @classmethod
    def from_yaml(cls, path: str | Path) -> AppConfig:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        raw = cls._apply_env_overrides(data)
        return cls.model_validate(raw)

    @classmethod
    def _apply_env_overrides(cls, data: dict) -> dict:
        prefix = "ZEMAX_AGENT_"
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            config_key = key[len(prefix):].lower()
            parts = config_key.split("__", 1)
            if len(parts) == 2:
                section, field = parts
                if section in data and isinstance(data[section], dict):
                    data[section][field] = cls._coerce_env_value(value)
            elif len(parts) == 1:
                data[parts[0]] = cls._coerce_env_value(value)
        return data

    @staticmethod
    def _coerce_env_value(value: str):
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        if value.lower() in ("none", "null", ""):
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value


_config: Optional[AppConfig] = None


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    global _config
    _config = AppConfig.from_yaml(path)
    return _config


def get_config() -> AppConfig:
    if _config is None:
        raise RuntimeError("Config not loaded. Call load_config() first.")
    return _config
