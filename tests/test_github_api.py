import json
from unittest.mock import MagicMock, patch

import pytest

from envkp.github_api import (
    GITHUB_API_BASE,
    api_delete,
    api_get,
    build_repo_url,
    check_delete_result,
)

HEADER = {"authorization": "token test"}


def _fake_urlopen(body, status_code=200, headers=None):
    """Return a context-manager mock that behaves like urlopen(...)."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.getcode.return_value = status_code
    resp.getheaders.return_value = headers or [("Content-Type", "application/json")]
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# build_repo_url
# ---------------------------------------------------------------------------

class TestBuildRepoUrl:
    def test_repo_only(self):
        assert build_repo_url("o/r") == f"{GITHUB_API_BASE}/repos/o/r"

    def test_single_segment(self):
        assert build_repo_url("o/r", "deployments") == "https://api.github.com/repos/o/r/deployments"

    def test_multiple_segments(self):
        assert (
            build_repo_url("o/r", "environments", "prod")
            == "https://api.github.com/repos/o/r/environments/prod"
        )

    def test_non_string_segments_are_stringified(self):
        assert build_repo_url("o/r", "deployments", 123) == "https://api.github.com/repos/o/r/deployments/123"


# ---------------------------------------------------------------------------
# api_get
# ---------------------------------------------------------------------------

class TestApiGet:
    @patch("envkp.github_api.urlopen")
    def test_returns_parsed_json_and_response(self, mock_urlopen):
        fake = _fake_urlopen([{"id": 1}])
        mock_urlopen.return_value = fake

        resjson, r = api_get("https://api.github.com/x", HEADER)

        assert resjson == [{"id": 1}]
        assert r is fake

    @patch("envkp.github_api.urlopen")
    def test_sends_get_request_with_headers(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen({})

        api_get("https://api.github.com/x", HEADER)

        req = mock_urlopen.call_args.args[0]
        assert req.get_method() == "GET"
        assert req.full_url == "https://api.github.com/x"
        assert req.get_header("Authorization") == "token test"

    @patch("envkp.github_api.urlopen")
    def test_propagates_http_error(self, mock_urlopen):
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError("u", 404, "Not Found", None, None)
        with pytest.raises(HTTPError):
            api_get("https://api.github.com/x", HEADER)


# ---------------------------------------------------------------------------
# api_delete
# ---------------------------------------------------------------------------

class TestApiDelete:
    @patch("envkp.github_api.urlopen")
    def test_returns_status_code(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen("", status_code=204)
        assert api_delete("https://api.github.com/x", HEADER) == 204

    @patch("envkp.github_api.urlopen")
    def test_sends_delete_request(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen("", status_code=204)

        api_delete("https://api.github.com/x", HEADER)

        req = mock_urlopen.call_args.args[0]
        assert req.get_method() == "DELETE"
        assert req.full_url == "https://api.github.com/x"


# ---------------------------------------------------------------------------
# check_delete_result
# ---------------------------------------------------------------------------

class TestCheckDeleteResult:
    def test_success_on_204(self, capsys):
        check_delete_result(204, "environment prod")
        assert "Done, 204" in capsys.readouterr().out

    @pytest.mark.parametrize("code", [200, 404, 422, 500])
    def test_error_on_non_204(self, code, capsys):
        check_delete_result(code, "environment prod")
        assert "Error deleting environment prod" in capsys.readouterr().out
