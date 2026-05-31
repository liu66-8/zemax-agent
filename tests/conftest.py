"""Pytest configuration and shared fixtures for zemax-agent tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from zemax_agent.config.settings import ConfigManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_path(temp_dir: Path) -> Path:
    return temp_dir / "config.yaml"


@pytest.fixture
def reset_config_manager() -> Generator[None, None, None]:
    ConfigManager.reset()
    yield
    ConfigManager.reset()


@pytest.fixture(autouse=True)
def clean_env() -> Generator[None, None, None]:
    saved = {}
    prefixes = [
        "ZEMAX_AGENT_",
    ]
    for key, value in os.environ.items():
        for prefix in prefixes:
            if key.startswith(prefix):
                saved[key] = value
                break

    for key in saved:
        if key in os.environ:
            del os.environ[key]

    yield

    for key in saved:
        if key in os.environ:
            del os.environ[key]
    for key, value in saved.items():
        os.environ[key] = value
