"""Shared pytest fixtures for Evolution test suite."""

import os
import sys
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure evolution package is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Prevent settings.py from creating real directories on import
os.environ.setdefault("EVOLUTION_ROOT", "/tmp/evolution_test_root")


@pytest.fixture(autouse=True)
def _reset_db_singleton():
    """Reset DatabaseManager singleton before each test."""
    from evolution.db.manager import DatabaseManager
    DatabaseManager._instance = None
    yield
    DatabaseManager._instance = None


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a temporary SQLite database path."""
    return str(tmp_path / "test_evolution.db")


@pytest.fixture
def db(tmp_db_path):
    """Provide a fresh DatabaseManager instance backed by a temp file."""
    from evolution.db.manager import DatabaseManager
    return DatabaseManager(tmp_db_path)


@pytest.fixture
def db_tool(tmp_db_path):
    """Provide an EvolutionDBTool wired to a temp database."""
    from evolution.tools.db_tool import EvolutionDBTool
    tool = EvolutionDBTool(config={"db_path": tmp_db_path})
    return tool


@pytest.fixture
def memory_tool():
    """Provide an EvolutionMemoryTool that falls back to MockMemory."""
    from evolution.tools.memory_tool import EvolutionMemoryTool, MockMemory
    tool = EvolutionMemoryTool()
    tool._memory = MockMemory()
    tool._user_id = "test_user"
    return tool


@pytest.fixture
def reflection_tool(tmp_db_path):
    """Provide an EvolutionReflectionTool wired to a temp database."""
    from evolution.tools.reflection_tool import EvolutionReflectionTool
    tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
    return tool


@pytest.fixture
def intelligence_tool():
    """Provide an EvolutionIntelligenceTool."""
    from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
    tool = EvolutionIntelligenceTool()
    return tool


@pytest.fixture
def notification_config():
    """Return a notification config with all channels enabled (for testing)."""
    return {
        "email": {
            "enabled": True,
            "smtp_server": "smtp.test.com",
            "smtp_port": 465,
            "username": "test@test.com",
            "password": "secret",
            "to_address": "user@test.com",
            "subject_prefix": "[Test]",
        },
        "telegram": {
            "enabled": True,
            "bot_token": "fake-token",
            "chat_id": "12345",
        },
        "notion": {
            "enabled": True,
            "token": "fake-notion-token",
            "databases": {
                "reflection": "db-reflection-id",
                "schedule": "db-schedule-id",
                "intelligence": "db-intel-id",
                "report": "db-report-id",
            },
        },
    }
