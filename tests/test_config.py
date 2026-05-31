import os
from pathlib import Path

import pytest
from zemax_agent.core.config import AppConfig, load_config, get_config


def test_appconfig_from_yaml(tmp_path: Path):
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text("""
llm:
  model: gpt-3.5-turbo
  api_key: test-key
zos:
  connection_mode: standalone
storage:
  db_path: ./test.db
project:
  workspace_dir: ./test_workspace
""", encoding="utf-8")

    config = AppConfig.from_yaml(config_path)
    assert config.llm.model == "gpt-3.5-turbo"
    assert config.zos.connection_mode == "standalone"
    assert config.storage.db_path == "./test.db"
    assert config.project.workspace_dir == "./test_workspace"


def test_appconfig_defaults():
    config = AppConfig()
    assert config.llm.model == "gpt-4"
    assert config.zos.connection_mode == "standalone"
    assert config.logging.level == "INFO"


def test_env_override(monkeypatch, tmp_path: Path):
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text("llm:\n  model: gpt-3.5-turbo", encoding="utf-8")

    monkeypatch.setenv("ZEMAX_AGENT_LLM__MODEL", "deepseek-v3")

    config = AppConfig.from_yaml(config_path)
    assert config.llm.model == "deepseek-v3"


def test_env_override_top_level(monkeypatch):
    monkeypatch.setenv("ZEMAX_AGENT_WORKSPACE_DIR", "./env_workspace")
    config = AppConfig()
    assert config.workspace_dir == "./env_workspace"
