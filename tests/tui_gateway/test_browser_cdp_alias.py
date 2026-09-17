"""Browser status uses the same pure endpoint precedence as browser tools."""
import json
import subprocess
import urllib.request

import pytest
import requests


@pytest.mark.parametrize("canonical", ["", "   ", "http://canonical.invalid:9222"])
def test_browser_status_alias_precedence_without_io(tmp_path, monkeypatch, canonical):
    from tui_gateway import server
    from tools.browser_tool_cdp import _get_cdp_override_raw

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    (tmp_path / "config.yaml").write_text(json.dumps({"browser": {
        "cdp_url": canonical, "cdp_endpoint": "http://alias.invalid:9222",
        "cdp_auto_launch": True, "cdp_launch_command": ["helper"],
    }}))

    def forbidden(*args, **kwargs):
        pytest.fail("status must not probe or launch")

    monkeypatch.setattr(requests, "get", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    for env_url in ("", "http://env.invalid:9222"):
        monkeypatch.setenv("BROWSER_CDP_URL", env_url)
        result = server.handle_request({"id": "alias", "method": "browser.manage",
                                        "params": {"action": "status"}})["result"]
        assert result == {"connected": True, "url": _get_cdp_override_raw()}
