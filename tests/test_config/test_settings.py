"""Tests for configuration management module."""

from __future__ import annotations

import os

import yaml

from zemax_agent.config.settings import AppConfig, ConfigManager


class TestDefaultConfig:
    def test_default_config_creates_all_sections(self, reset_config_manager, temp_config_path):
        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        assert isinstance(config, AppConfig)
        assert config.zemax.connection_mode == "standalone"
        assert config.zemax.connection_timeout == 30.0
        assert config.zemax.auto_reconnect is True
        assert config.zemax.max_reconnect_attempts == 3

        assert config.llm.provider == "openai"
        assert config.llm.api_key == ""
        assert config.llm.model == "gpt-4"
        assert config.llm.temperature == 0.1

        assert config.optimization.max_iterations == 100
        assert config.optimization.convergence_threshold == 1e-6

        assert config.tolerance.default_sample_count == 500

        assert config.workspace_dir == "./workspace"
        assert config.log_level == "INFO"

    def test_default_config_created_when_file_missing(
        self, reset_config_manager, temp_config_path
    ):
        assert not temp_config_path.exists()

        mgr = ConfigManager(str(temp_config_path))
        mgr.load()

        assert temp_config_path.exists()
        content = temp_config_path.read_text(encoding="utf-8")
        assert "connection_mode" in content
        assert "api_key" in content


class TestYamlLoad:
    def test_load_from_yaml_file(self, reset_config_manager, temp_config_path):
        yaml_data = {
            "zemax": {"connection_mode": "extension", "connection_timeout": 60.0},
            "llm": {"model": "gpt-3.5-turbo", "temperature": 0.5},
            "workspace_dir": "/custom/workspace",
            "log_level": "DEBUG",
        }
        temp_config_path.write_text(yaml.dump(yaml_data), encoding="utf-8")

        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        assert config.zemax.connection_mode == "extension"
        assert config.zemax.connection_timeout == 60.0
        assert config.zemax.auto_reconnect is True
        assert config.llm.model == "gpt-3.5-turbo"
        assert config.llm.temperature == 0.5
        assert config.llm.provider == "openai"
        assert config.workspace_dir == "/custom/workspace"
        assert config.log_level == "DEBUG"

    def test_nested_section_partial_override(self, reset_config_manager, temp_config_path):
        yaml_data = {
            "optimization": {"auto_hammer": True},
        }
        temp_config_path.write_text(yaml.dump(yaml_data), encoding="utf-8")

        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        assert config.optimization.auto_hammer is True
        assert config.optimization.max_iterations == 100
        assert config.optimization.convergence_threshold == 1e-6


class TestEnvOverride:
    def test_env_overrides_top_level(self, reset_config_manager, temp_config_path):
        os.environ["ZEMAX_AGENT_LOG_LEVEL"] = "ERROR"
        os.environ["ZEMAX_AGENT_WORKSPACE_DIR"] = "/env/workspace"

        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        assert config.log_level == "ERROR"
        assert config.workspace_dir == "/env/workspace"

    def test_env_overrides_nested_section(self, reset_config_manager, temp_config_path):
        os.environ["ZEMAX_AGENT_LLM__MODEL"] = "gpt-4-turbo"
        os.environ["ZEMAX_AGENT_LLM__API_KEY"] = "sk-env-key"
        os.environ["ZEMAX_AGENT_ZEMAX__CONNECTION_MODE"] = "extension"

        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        assert config.llm.model == "gpt-4-turbo"
        assert config.llm.api_key == "sk-env-key"
        assert config.zemax.connection_mode == "extension"

    def test_env_overrides_yaml_values(self, reset_config_manager, temp_config_path):
        yaml_data = {
            "llm": {"model": "yaml-model", "api_key": "yaml-key"},
            "log_level": "WARNING",
        }
        temp_config_path.write_text(yaml.dump(yaml_data), encoding="utf-8")

        os.environ["ZEMAX_AGENT_LLM__MODEL"] = "env-model"
        os.environ["ZEMAX_AGENT_LOG_LEVEL"] = "ERROR"

        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        assert config.llm.model == "env-model"
        assert config.llm.api_key == "yaml-key"
        assert config.log_level == "ERROR"

    def test_unknown_env_var_ignored(self, reset_config_manager, temp_config_path):
        os.environ["ZEMAX_AGENT_UNKNOWN_KEY"] = "should-be-ignored"
        os.environ["ZEMAX_AGENT_UNKNOWN__KEY"] = "also-ignored"

        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        assert config.log_level == "INFO"

    def test_priority_env_beats_yaml_beats_default(self, reset_config_manager, temp_config_path):
        yaml_data = {"llm": {"temperature": 0.7}}
        temp_config_path.write_text(yaml.dump(yaml_data), encoding="utf-8")

        os.environ["ZEMAX_AGENT_LLM__TEMPERATURE"] = "0.2"

        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        assert config.llm.temperature == 0.2


class TestConfigSave:
    def test_save_creates_file(self, reset_config_manager, temp_config_path):
        mgr = ConfigManager(str(temp_config_path))
        mgr.load()
        mgr.save()

        assert temp_config_path.exists()

    def test_save_preserves_values(self, reset_config_manager, temp_config_path):
        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()

        config.llm.model = "saved-model"
        config.log_level = "DEBUG"

        mgr.save()

        mgr2 = ConfigManager(str(temp_config_path))
        config2 = mgr2.load()

        assert config2.llm.model == "saved-model"
        assert config2.log_level == "DEBUG"

    def test_get_returns_same_instance(self, reset_config_manager, temp_config_path):
        mgr = ConfigManager(str(temp_config_path))
        config1 = mgr.get()
        config2 = mgr.get()

        assert config1 is config2

    def test_load_after_get_returns_consistent(self, reset_config_manager, temp_config_path):
        mgr = ConfigManager(str(temp_config_path))
        config = mgr.load()
        config2 = mgr.get()

        assert config is config2
