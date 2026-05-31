"""Tests for Zemax ZOS-API connection management module.

All tests use real code paths without mocking. In a no-Zemax environment,
connect() raises ImportError, which is the expected and tested behavior.
"""

from __future__ import annotations

import os

import pytest

from zemax_agent.api.connection import ConnectionMode, ZemaxConnection
from zemax_agent.api.session import ZemaxSession


def _nonexistent_zemax_path() -> str:
    return os.path.join(os.path.abspath(os.sep), "nonexistent_zemax_path_12345")


def _set_zemax_env(path: str | None = None) -> None:
    if path is None:
        path = _nonexistent_zemax_path()
    os.environ["ZEMAX_PATH"] = path


def _clear_zemax_env() -> None:
    os.environ.pop("ZEMAX_PATH", None)


class TestConnectionMode:
    def test_standalone_value(self):
        assert ConnectionMode.STANDALONE.value == "standalone"

    def test_extension_value(self):
        assert ConnectionMode.EXTENSION.value == "extension"

    def test_members_count(self):
        members = list(ConnectionMode)
        assert len(members) == 2

    def test_from_string_standalone(self):
        assert ConnectionMode("standalone") == ConnectionMode.STANDALONE

    def test_from_string_extension(self):
        assert ConnectionMode("extension") == ConnectionMode.EXTENSION


class TestZemaxConnectionInit:
    def test_default_values(self):
        conn = ZemaxConnection()
        assert conn.mode == ConnectionMode.STANDALONE
        assert conn.timeout == 30.0
        assert conn.auto_reconnect is True
        assert conn.max_reconnect_attempts == 3
        assert conn._zosapi is None
        assert conn._zosapi_app is None
        assert conn._the_system is None
        assert conn._connected is False

    def test_custom_values(self):
        conn = ZemaxConnection(
            mode=ConnectionMode.EXTENSION,
            timeout=60.0,
            auto_reconnect=False,
            max_reconnect_attempts=5,
        )
        assert conn.mode == ConnectionMode.EXTENSION
        assert conn.timeout == 60.0
        assert conn.auto_reconnect is False
        assert conn.max_reconnect_attempts == 5


class TestIsConnected:
    def test_not_connected_initially(self):
        conn = ZemaxConnection()
        assert conn.is_connected is False

    def test_not_connected_before_connect(self):
        conn = ZemaxConnection()
        conn._connected = False
        conn._zosapi_app = object()
        assert conn.is_connected is False

    def test_connected_when_flag_set_and_app_exists(self):
        conn = ZemaxConnection()
        conn._connected = True
        conn._zosapi_app = object()
        assert conn.is_connected is True

    def test_app_none_does_not_affect_is_connected_flag(self):
        conn = ZemaxConnection()
        conn._connected = True
        conn._zosapi_app = None
        assert conn.is_connected is True


class TestPropertiesWhenNotConnected:
    def test_zosapi_raises_connection_error(self):
        conn = ZemaxConnection()
        with pytest.raises(ConnectionError, match="未连接到 Zemax"):
            _ = conn.zosapi

    def test_app_raises_connection_error(self):
        conn = ZemaxConnection()
        with pytest.raises(ConnectionError, match="未连接到 Zemax"):
            _ = conn.app

    def test_system_raises_connection_error(self):
        conn = ZemaxConnection()
        with pytest.raises(ConnectionError, match="未连接到 Zemax"):
            _ = conn.system


class TestConnectMissingDLL:
    def test_connect_raises_import_error_when_dll_missing(self):
        _set_zemax_env()
        try:
            conn = ZemaxConnection()
            with pytest.raises(ImportError):
                conn.connect()
        finally:
            _clear_zemax_env()

    def test_connect_error_message_contains_path_info(self):
        fake_path = _nonexistent_zemax_path()
        _set_zemax_env(fake_path)
        try:
            conn = ZemaxConnection()
            with pytest.raises(ImportError) as exc_info:
                conn.connect()
            error_msg = str(exc_info.value)
            assert "ZOSAPI_NetHelper.dll" in error_msg or "clr" in error_msg.lower()
        finally:
            _clear_zemax_env()

    def test_connect_does_not_leave_connected_state_on_failure(self):
        _set_zemax_env()
        try:
            conn = ZemaxConnection()
            try:
                conn.connect()
            except (ImportError, ConnectionError):
                pass
            assert conn.is_connected is False
            assert conn._connected is False
        finally:
            _clear_zemax_env()


class TestDisconnect:
    def test_disconnect_when_not_connected_is_safe(self):
        conn = ZemaxConnection()
        conn.disconnect()
        assert conn.is_connected is False
        assert conn._zosapi is None
        assert conn._zosapi_app is None
        assert conn._the_system is None

    def test_disconnect_cleans_up_all_state(self):
        conn = ZemaxConnection()
        conn._connected = True
        conn._zosapi = object()
        conn._zosapi_app = object()
        conn._the_system = object()
        conn.disconnect()
        assert conn._connected is False
        assert conn._zosapi is None
        assert conn._zosapi_app is None
        assert conn._the_system is None


class TestEnsureConnected:
    def test_auto_reconnect_disabled_raises_error(self):
        conn = ZemaxConnection(auto_reconnect=False)
        with pytest.raises(ConnectionError, match="自动重连已禁用"):
            conn.ensure_connected()

    def test_auto_reconnect_disabled_after_disconnect(self):
        conn = ZemaxConnection(auto_reconnect=False)
        conn._connected = True
        conn._zosapi_app = object()
        assert conn.is_connected is True
        conn.disconnect()
        assert conn.is_connected is False
        with pytest.raises(ConnectionError, match="自动重连已禁用"):
            conn.ensure_connected()


class TestContextManager:
    def test_enter_raises_import_error_in_no_zemax_env(self):
        _set_zemax_env()
        try:
            conn = ZemaxConnection()
            with pytest.raises(ImportError):
                conn.__enter__()
        finally:
            _clear_zemax_env()

    def test_context_manager_not_connected_after_failed_enter(self):
        _set_zemax_env()
        try:
            conn = ZemaxConnection()
            try:
                with conn:
                    pass
            except ImportError:
                pass
            assert conn.is_connected is False
        finally:
            _clear_zemax_env()

    def test_exit_disconnects(self):
        conn = ZemaxConnection()
        conn._connected = True
        conn._zosapi_app = object()
        conn.__exit__(None, None, None)
        assert conn._connected is False
        assert conn._zosapi_app is None


class TestReconnect:
    def test_reconnect_in_no_zemax_env_raises(self):
        _set_zemax_env()
        try:
            conn = ZemaxConnection()
            with pytest.raises(ImportError):
                conn.reconnect()
            assert conn.is_connected is False
        finally:
            _clear_zemax_env()


class TestZemaxSession:
    def test_initialization_state(self):
        session = ZemaxSession()
        assert session._connection is None
        assert session.connection is None
        assert session.is_active is False

    def test_is_active_when_no_connection(self):
        session = ZemaxSession()
        assert session.is_active is False

    def test_close_when_no_connection_is_safe(self):
        session = ZemaxSession()
        session.close()
        assert session.is_active is False

    def test_open_fails_in_no_zemax_env(self):
        _set_zemax_env()
        try:
            session = ZemaxSession()
            with pytest.raises(ImportError):
                session.open()
            assert session.is_active is False
        finally:
            _clear_zemax_env()

    def test_session_context_manager_protocol(self):
        session = ZemaxSession()
        assert session.__enter__() is session
        session.__exit__(None, None, None)
        assert session.is_active is False
