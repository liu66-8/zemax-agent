"""Configuration management module.

Handles loading, validation, and management of system configuration
via YAML files and Pydantic models.
"""

from zemax_agent.config.logging_config import setup_logging
from zemax_agent.config.settings import AppConfig, ConfigManager

__all__ = ["AppConfig", "ConfigManager", "setup_logging"]
