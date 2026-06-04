import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def clear_cdp_resolution_cache():
    import tools.browser_tool as browser_tool

    browser_tool._cached_cdp_resolutions.clear()
    yield
    browser_tool._cached_cdp_resolutions.clear()


HOST = "example-host"
PORT = 9223
WS_URL = f"ws://{HOST}:{PORT}/devtools/browser/abc123"
HTTP_URL = f"http://{HOST}:{PORT}"
VERSION_URL = f"{HTTP_URL}/json/version"


class TestResolveCdpOverride:
    def test_keeps_full_devtools_websocket_url(self):
        from tools.browser_tool import _resolve_cdp_override

        assert _resolve_cdp_override(WS_URL) == WS_URL

    def test_resolves_http_discovery_endpoint_to_websocket(self):
        from tools.browser_tool import _resolve_cdp_override

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = _resolve_cdp_override(HTTP_URL)

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=10)

    def test_resolves_bare_ws_hostport_to_discovery_websocket(self):
        from tools.browser_tool import _resolve_cdp_override

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = _resolve_cdp_override(f"ws://{HOST}:{PORT}")

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=10)

    def test_falls_back_to_raw_url_when_discovery_fails(self):
        from tools.browser_tool import _resolve_cdp_override

        with patch("tools.browser_tool.requests.get", side_effect=RuntimeError("boom")):
            assert _resolve_cdp_override(HTTP_URL) == HTTP_URL

    def test_returns_empty_when_discovery_fails_without_raw_fallback(self):
        from tools.browser_tool import _resolve_cdp_override

        with patch("tools.browser_tool.requests.get", side_effect=RuntimeError("boom")):
            assert _resolve_cdp_override(HTTP_URL, fallback_to_raw=False) == ""

    def test_uses_short_timeout_for_explicit_startup_probe(self):
        from tools.browser_tool import _resolve_cdp_override

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = _resolve_cdp_override(HTTP_URL, timeout=0.5, fallback_to_raw=False)

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=0.5)

    def test_normalizes_provider_returned_http_cdp_url_when_creating_session(self, monkeypatch):
        import tools.browser_tool as browser_tool

        provider = Mock()
        provider.create_session.return_value = {
            "session_name": "cloud-session",
            "bb_session_id": "bu_123",
            "cdp_url": "https://cdp.browser-use.example/session",
            "features": {"browser_use": True},
        }

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        monkeypatch.setattr(browser_tool, "_active_sessions", {})
        monkeypatch.setattr(browser_tool, "_session_last_activity", {})
        monkeypatch.setattr(browser_tool, "_start_browser_cleanup_thread", lambda: None)
        monkeypatch.setattr(browser_tool, "_update_session_activity", lambda task_id: None)
        monkeypatch.setattr(browser_tool, "_get_cdp_override", lambda: "")
        monkeypatch.setattr(browser_tool, "_get_cloud_provider", lambda: provider)

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            session_info = browser_tool._get_session_info("task-browser-use")

        assert session_info["cdp_url"] == WS_URL
        provider.create_session.assert_called_once_with("task-browser-use")
        mock_get.assert_called_once_with(
            "https://cdp.browser-use.example/session/json/version",
            timeout=10,
        )


class TestGetCdpOverride:
    def test_prefers_env_var_over_config(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.setenv("BROWSER_CDP_URL", HTTP_URL)
        monkeypatch.setattr(
            browser_tool,
            "read_raw_config",
            lambda: {"browser": {"cdp_url": "http://config-host:9222"}},
            raising=False,
        )

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = browser_tool._get_cdp_override()

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=10)

    def test_uses_config_browser_cdp_url_when_env_missing(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}

        with patch("hermes_cli.config.read_raw_config", return_value={"browser": {"cdp_url": HTTP_URL}}), \
             patch("tools.browser_tool.requests.get", return_value=response) as mock_get:
            resolved = browser_tool._get_cdp_override()

        assert resolved == WS_URL
        mock_get.assert_called_once_with(VERSION_URL, timeout=10)

    def test_lazy_launches_configured_cdp_browser_on_first_use(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"webSocketDebuggerUrl": WS_URL}
        proc = Mock(returncode=0, stdout="ready", stderr="")

        with patch(
            "hermes_cli.config.read_raw_config",
            return_value={
                "browser": {
                    "cdp_url": HTTP_URL,
                    "cdp_auto_launch": True,
                    "cdp_launch_command": "/tmp/start-cdp --port 9223",
                }
            },
        ), patch(
            "tools.browser_tool.requests.get",
            side_effect=[RuntimeError("connection refused"), response],
        ) as mock_get, patch("tools.browser_tool.subprocess.run", return_value=proc) as mock_run:
            resolved = browser_tool._get_cdp_override()

        assert resolved == WS_URL
        assert mock_get.call_args_list[0].args == (VERSION_URL,)
        assert mock_get.call_args_list[0].kwargs == {"timeout": 1.0}
        assert mock_get.call_args_list[1].args == (VERSION_URL,)
        assert mock_get.call_args_list[1].kwargs == {"timeout": 10}
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == ["/tmp/start-cdp", "--port", "9223"]

    def test_does_not_lazy_launch_when_disabled(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
        with patch(
            "hermes_cli.config.read_raw_config",
            return_value={
                "browser": {
                    "cdp_url": HTTP_URL,
                    "cdp_auto_launch": False,
                    "cdp_launch_command": "/tmp/start-cdp",
                }
            },
        ), patch("tools.browser_tool.requests.get", side_effect=RuntimeError("down")), patch(
            "tools.browser_tool.subprocess.run"
        ) as mock_run:
            resolved = browser_tool._get_cdp_override()

        assert resolved == HTTP_URL
        mock_run.assert_not_called()

    def test_is_local_mode_does_not_probe_or_launch_configured_cdp(self, monkeypatch):
        import tools.browser_tool as browser_tool

        monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
        with patch(
            "hermes_cli.config.read_raw_config",
            return_value={
                "browser": {
                    "cdp_url": HTTP_URL,
                    "cdp_auto_launch": True,
                    "cdp_launch_command": "/tmp/start-cdp",
                }
            },
        ), patch("tools.browser_tool.requests.get") as mock_get, patch(
            "tools.browser_tool.subprocess.run"
        ) as mock_run:
            assert browser_tool._is_local_mode() is False

        mock_get.assert_not_called()
        mock_run.assert_not_called()
