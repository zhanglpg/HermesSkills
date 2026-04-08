"""Tests for wiki-manager logging_utils module."""

import logging

from logging_utils import get_agent_data_dir, setup_logger


class TestGetAgentDataDir:
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("AGENT_DATA_DIR", "/custom/path")
        assert get_agent_data_dir() == "/custom/path"

    def test_fallback(self, monkeypatch):
        monkeypatch.delenv("AGENT_DATA_DIR", raising=False)
        result = get_agent_data_dir()
        assert ".openclaw" in result


class TestSetupLogger:
    def test_returns_logger(self):
        logger = setup_logger("test-logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test-logger"

    def test_has_console_handler(self):
        logger = setup_logger("test-console")
        handler_types = [type(h) for h in logger.handlers]
        assert logging.StreamHandler in handler_types
