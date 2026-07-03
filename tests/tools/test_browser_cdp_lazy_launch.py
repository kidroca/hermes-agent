from unittest.mock import Mock, patch

import pytest


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


class TestCdpLazyLaunch:
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
