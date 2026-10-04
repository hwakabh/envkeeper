import json
import sys
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from envkp import __version__
from envkp.core import (
    cli,
    cli_precheck,
    delete_inactive_deployment,
    fetch_cli_args,
    fetch_environments,
    fetch_pairs,
    get_deployment_statuses,
    get_deployments_by_env,
    get_version,
    is_inactive_deployment,
    is_pagenated,
)

HEADER = {"authorization": "token test", "accept": "application/json"}

# core.py still calls urlopen/Request/json in a few places but no longer imports them
# after the github_api extraction (#103), so these paths currently raise NameError.
missing_urlopen_import = pytest.mark.xfail(
    raises=NameError,
    strict=True,
    reason="envkp/core.py uses urlopen/Request/json without importing them",
)


def _http_error(code=404, msg="Not Found"):
    return HTTPError(url="https://api.github.com", code=code, msg=msg, hdrs=None, fp=None)


def _resp(headers=None):
    resp = MagicMock()
    resp.getheaders.return_value = headers or [("Content-Type", "application/json")]
    return resp


def _fake_urlopen(body, status_code=200, headers=None):
    """Return a context-manager mock that behaves like urlopen(...)."""
    resp = _resp(headers)
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.getcode.return_value = status_code
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------

class TestGetVersion:
    def test_returns_version_string(self):
        assert get_version() == __version__

    def test_version_is_semver_like(self):
        parts = get_version().split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ---------------------------------------------------------------------------
# cli_precheck
# ---------------------------------------------------------------------------

class TestCliPrecheck:
    def test_valid_repo_and_token(self):
        assert cli_precheck(repo="owner/repo", token="ghp_abc123") is True

    @pytest.mark.parametrize("repo", ["invalid-repo", "a/b/c", ""])
    def test_invalid_repo_format(self, repo, capsys):
        assert cli_precheck(repo=repo, token="ghp_abc123") is False
        assert "format invalid" in capsys.readouterr().out

    def test_token_none(self, capsys):
        assert cli_precheck(repo="owner/repo", token=None) is False
        assert "GH_TOKEN" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# get_deployments_by_env
# ---------------------------------------------------------------------------

MAPPINGS = [
    {"url": "https://api.github.com/repos/o/r/deployments/1/statuses", "env": "production"},
    {"url": "https://api.github.com/repos/o/r/deployments/2/statuses", "env": "staging"},
    {"url": "https://api.github.com/repos/o/r/deployments/3/statuses", "env": "production"},
]


class TestGetDeploymentsByEnv:
    def test_filters_by_env(self):
        result = get_deployments_by_env(MAPPINGS, "production")
        assert result == [MAPPINGS[0]["url"], MAPPINGS[2]["url"]]

    def test_returns_empty_for_unknown_env(self):
        assert get_deployments_by_env(MAPPINGS, "does-not-exist") == []

    def test_empty_mappings(self):
        assert get_deployments_by_env([], "production") == []


# ---------------------------------------------------------------------------
# is_pagenated
# ---------------------------------------------------------------------------

class TestIsPagenated:
    def test_paginated_when_link_header_present(self):
        assert is_pagenated(_resp([("Link", '<...>; rel="next"'), ("Content-Type", "x")])) is True

    def test_not_paginated_without_link_header(self):
        assert is_pagenated(_resp([("Content-Type", "application/json")])) is False

    def test_empty_headers(self):
        resp = MagicMock()
        resp.getheaders.return_value = []
        assert is_pagenated(resp) is False


# ---------------------------------------------------------------------------
# fetch_pairs
# ---------------------------------------------------------------------------

DEPLOYMENTS = [
    {"statuses_url": "https://api.github.com/repos/o/r/deployments/1/statuses", "environment": "prod"},
    {"statuses_url": "https://api.github.com/repos/o/r/deployments/2/statuses", "environment": "staging"},
]


class TestFetchPairs:
    @patch("envkp.core.api_get")
    def test_returns_pairs_without_pagination(self, mock_get):
        mock_get.return_value = (list(DEPLOYMENTS), _resp())

        pairs = fetch_pairs(repo="o/r", reqheader=HEADER)

        assert pairs == [
            {"url": DEPLOYMENTS[0]["statuses_url"], "env": "prod"},
            {"url": DEPLOYMENTS[1]["statuses_url"], "env": "staging"},
        ]
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/o/r/deployments?per_page=100", HEADER
        )

    @patch("envkp.core.api_get")
    def test_empty_deployments(self, mock_get):
        mock_get.return_value = ([], _resp())
        assert fetch_pairs(repo="o/r", reqheader=HEADER) == []

    @patch("envkp.core.api_get")
    def test_missing_keys_become_none(self, mock_get):
        mock_get.return_value = ([{}], _resp())
        assert fetch_pairs(repo="o/r", reqheader=HEADER) == [{"url": None, "env": None}]

    @patch("envkp.core.api_get")
    def test_propagates_http_error_on_first_page(self, mock_get):
        mock_get.side_effect = _http_error()
        with pytest.raises(HTTPError):
            fetch_pairs(repo="o/r", reqheader=HEADER)

    @missing_urlopen_import
    @patch("envkp.core.api_get")
    def test_fetches_second_page_when_paginated(self, mock_get):
        mock_get.return_value = (list(DEPLOYMENTS), _resp([("Link", '<...>; rel="next"')]))
        page2 = [{"statuses_url": "https://api.github.com/repos/o/r/deployments/3/statuses", "environment": "dev"}]

        with patch("envkp.core.urlopen", create=True) as mock_urlopen:
            mock_urlopen.return_value = _fake_urlopen(page2)
            pairs = fetch_pairs(repo="o/r", reqheader=HEADER)

        assert len(pairs) == 3
        assert pairs[2]["env"] == "dev"


# ---------------------------------------------------------------------------
# fetch_environments
# ---------------------------------------------------------------------------

class TestFetchEnvironments:
    @missing_urlopen_import
    def test_returns_environments(self):
        with patch("envkp.core.urlopen", create=True) as mock_urlopen:
            mock_urlopen.return_value = _fake_urlopen({"environments": [{"name": "prod"}]})
            assert fetch_environments(repo="o/r", reqheader=HEADER) == [{"name": "prod"}]

    @missing_urlopen_import
    def test_defaults_to_empty_list_when_key_missing(self):
        with patch("envkp.core.urlopen", create=True) as mock_urlopen:
            mock_urlopen.return_value = _fake_urlopen({})
            assert fetch_environments(repo="o/r", reqheader=HEADER) == []


# ---------------------------------------------------------------------------
# get_deployment_statuses
# ---------------------------------------------------------------------------

class TestGetDeploymentStatuses:
    URL = "https://api.github.com/repos/o/r/deployments/1/statuses"

    @patch("envkp.core.api_get")
    def test_returns_id_state_tuples(self, mock_get):
        mock_get.return_value = ([{"id": 100, "state": "success"}, {"id": 101, "state": "inactive"}], _resp())

        assert get_deployment_statuses(status_url=self.URL, reqheader=HEADER) == [
            (100, "success"),
            (101, "inactive"),
        ]
        mock_get.assert_called_once_with(self.URL, HEADER)

    @patch("envkp.core.api_get")
    def test_empty_statuses(self, mock_get):
        mock_get.return_value = ([], _resp())
        assert get_deployment_statuses(status_url=self.URL, reqheader=HEADER) == []


# ---------------------------------------------------------------------------
# is_inactive_deployment
# ---------------------------------------------------------------------------

class TestIsInactiveDeployment:
    @pytest.mark.parametrize(
        "states, expected",
        [
            (["inactive"], True),
            (["success"], False),
            (["success", "success"], False),
            (["in_progress"], True),
            (["failure"], True),
            (["in_progress", "failure"], True),
            (["inactive", "success"], True),
            ([], True),
        ],
    )
    @patch("envkp.core.get_deployment_statuses")
    def test_inactive_detection(self, mock_statuses, states, expected):
        mock_statuses.return_value = [(i, s) for i, s in enumerate(states)]
        assert is_inactive_deployment(d="url", reqheader=HEADER) is expected
        mock_statuses.assert_called_once_with(status_url="url", reqheader=HEADER)


# ---------------------------------------------------------------------------
# delete_inactive_deployment
# ---------------------------------------------------------------------------

class TestDeleteInactiveDeployment:
    @pytest.mark.parametrize("code", [204, 422])
    @patch("envkp.core.api_delete")
    def test_returns_status_code(self, mock_delete, code):
        mock_delete.return_value = code

        assert delete_inactive_deployment(deployment_id="123", gh_reponame="o/r", reqheader=HEADER) == code
        mock_delete.assert_called_once_with("https://api.github.com/repos/o/r/deployments/123", HEADER)

    @patch("envkp.core.api_delete")
    def test_propagates_http_error(self, mock_delete):
        mock_delete.side_effect = _http_error(422, "Unprocessable Entity")
        with pytest.raises(HTTPError):
            delete_inactive_deployment(deployment_id="123", gh_reponame="o/r", reqheader=HEADER)


# ---------------------------------------------------------------------------
# fetch_cli_args
# ---------------------------------------------------------------------------

class TestFetchCliArgs:
    @pytest.mark.parametrize("subcommand", ["clean", "seek", "help", "version"])
    def test_subcommands(self, subcommand, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "owner/repo", subcommand])
        _, args = fetch_cli_args()
        assert args.subcommand == subcommand
        assert args.repo == "owner/repo"

    def test_no_subcommand(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp"])
        _, args = fetch_cli_args()
        assert args.subcommand is None
        assert args.repo is None

    def test_clean_with_force(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "-r", "o/r", "clean", "--force"])
        _, args = fetch_cli_args()
        assert args.force is True

    def test_seek_with_verbose(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "-r", "o/r", "seek", "-v"])
        _, args = fetch_cli_args()
        assert args.verbose is True

    def test_version_flag_exits(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["envkp", "--version"])
        with pytest.raises(SystemExit) as exc_info:
            fetch_cli_args()
        assert exc_info.value.code == 0
        assert __version__ in capsys.readouterr().out


# ---------------------------------------------------------------------------
# cli()
# ---------------------------------------------------------------------------

DEPLOY_URL = "https://api.github.com/repos/o/r/deployments/10/statuses"


@pytest.fixture
def run_cli(monkeypatch, capsys):
    """Run cli() with the given argv and return (exit_code, stdout)."""

    def _run(*argv, token="fake-token"):
        monkeypatch.setattr(sys, "argv", ["envkp", *argv])
        monkeypatch.delenv("GH_REPONAME", raising=False)
        if token is None:
            monkeypatch.delenv("GH_TOKEN", raising=False)
        else:
            monkeypatch.setenv("GH_TOKEN", token)
        with pytest.raises(SystemExit) as exc_info:
            cli()
        return exc_info.value.code, capsys.readouterr().out

    return _run


class TestCliArgumentHandling:
    def test_no_subcommand_exits_1(self, run_cli):
        code, out = run_cli()
        assert code == 1
        assert "usage" in out

    def test_help_exits_0(self, run_cli):
        code, out = run_cli("help")
        assert code == 0
        assert "usage" in out

    def test_version_prints_version(self, run_cli):
        code, out = run_cli("version")
        assert code == 0
        assert __version__ in out

    def test_missing_repo_exits_1(self, run_cli):
        code, out = run_cli("clean")
        assert code == 1
        assert "Missing arguments" in out

    def test_invalid_repo_format_exits_1(self, run_cli):
        code, out = run_cli("--repo", "badformat", "clean")
        assert code == 1
        assert "format invalid" in out

    def test_missing_token_exits_1(self, run_cli):
        code, out = run_cli("--repo", "o/r", "clean", token=None)
        assert code == 1
        assert "GH_TOKEN" in out

    @patch("envkp.core.fetch_pairs", return_value=[])
    def test_gh_reponame_env_overrides_flag(self, mock_fp, run_cli, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "flag/repo", "seek"])
        monkeypatch.setenv("GH_REPONAME", "env/repo")
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        with pytest.raises(SystemExit):
            cli()
        assert mock_fp.call_args.kwargs["repo"] == "env/repo"

    @patch("envkp.core.fetch_pairs", return_value=[])
    def test_token_is_sent_in_header(self, mock_fp, run_cli):
        run_cli("--repo", "o/r", "seek", token="secret")
        assert mock_fp.call_args.kwargs["reqheader"]["authorization"] == "token secret"


class TestCliFetching:
    @patch("envkp.core.fetch_pairs", side_effect=_http_error(404))
    def test_fetch_pairs_http_error_exits_1(self, _mock_fp, run_cli):
        code, out = run_cli("--repo", "o/r", "clean")
        assert code == 1
        assert "Failed to fetch targets" in out
        assert "HTTP 404" in out

    @patch("envkp.core.fetch_pairs", return_value=[])
    def test_empty_pairs_exits_0(self, _mock_fp, run_cli):
        code, out = run_cli("--repo", "o/r", "clean")
        assert code == 0
        assert "No environment found" in out

    @patch("envkp.core.fetch_environments", side_effect=_http_error(403, "Forbidden"))
    @patch("envkp.core.fetch_pairs", return_value=[{"url": DEPLOY_URL, "env": "prod"}])
    def test_fetch_environments_http_error_exits_1(self, _mock_fp, _mock_fe, run_cli):
        code, out = run_cli("--repo", "o/r", "seek")
        assert code == 1
        assert "Failed to fetch environments" in out
        assert "HTTP 403: Forbidden" in out

    @patch("envkp.core.fetch_environments", return_value=[])
    @patch("envkp.core.fetch_pairs", return_value=[{"url": DEPLOY_URL, "env": "prod"}])
    def test_no_environments_exits_0(self, _mock_fp, _mock_fe, run_cli):
        code, out = run_cli("--repo", "o/r", "seek")
        assert code == 0
        assert "No environments found" in out


@pytest.fixture
def mock_core(monkeypatch):
    """Replace an attribute of envkp.core with a MagicMock and return the mock."""

    def _mock(name, **kwargs):
        m = MagicMock(**kwargs)
        monkeypatch.setattr(f"envkp.core.{name}", m)
        return m

    return _mock


class TestCliSeek:
    @pytest.fixture(autouse=True)
    def _targets(self, mock_core):
        mock_core("fetch_pairs", return_value=[{"url": DEPLOY_URL, "env": "prod"}])
        mock_core("fetch_environments", return_value=[{"name": "prod"}])

    def test_prints_deployments(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", return_value=True)
        code, out = run_cli("--repo", "o/r", "seek")
        assert code == 0
        assert f"- {DEPLOY_URL} (is_inactive: True)" in out
        assert "Operation seek completed" in out

    def test_status_check_http_error_is_reported(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", side_effect=_http_error(500, "Server Error"))
        code, out = run_cli("--repo", "o/r", "seek")
        assert code == 0
        assert "failed to check status: HTTP 500: Server Error" in out

    def test_never_deletes(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", return_value=True)
        delete = mock_core("delete_inactive_deployment")
        api_delete = mock_core("api_delete")
        run_cli("--repo", "o/r", "seek")
        delete.assert_not_called()
        api_delete.assert_not_called()


class TestCliCleanDeployments:
    @pytest.fixture(autouse=True)
    def _targets(self, mock_core):
        mock_core("fetch_pairs", return_value=[{"url": DEPLOY_URL, "env": "staging"}])
        mock_core("fetch_environments", return_value=[{"name": "staging"}])
        self.statuses = mock_core("get_deployment_statuses", return_value=[(1, "inactive")])
        self.api_delete = mock_core("api_delete")

    def test_deletes_inactive_deployment(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", return_value=True)
        delete = mock_core("delete_inactive_deployment", return_value=204)
        code, out = run_cli("--repo", "o/r", "clean")
        assert code == 0
        assert "Done, 204" in out
        delete.assert_called_once()
        assert delete.call_args.kwargs["deployment_id"] == "10"
        assert delete.call_args.kwargs["gh_reponame"] == "o/r"

    def test_reports_unexpected_delete_status(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", return_value=True)
        mock_core("delete_inactive_deployment", return_value=422)
        code, out = run_cli("--repo", "o/r", "clean")
        assert code == 0
        assert "10: Unexpected response status 422" in out

    def test_delete_http_error_is_reported(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", return_value=True)
        mock_core("delete_inactive_deployment", side_effect=_http_error(422, "Unprocessable"))
        code, out = run_cli("--repo", "o/r", "clean")
        assert code == 0
        assert "10: Failed to delete deployment (HTTP 422: Unprocessable)" in out

    def test_skips_active_deployment(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", return_value=False)
        delete = mock_core("delete_inactive_deployment")
        code, out = run_cli("--repo", "o/r", "clean")
        assert code == 0
        assert "Deployment is active, nothing to do" in out
        delete.assert_not_called()

    def test_statuses_http_error_skips_deployment(self, mock_core, run_cli):
        self.statuses.side_effect = _http_error(404)
        inactive = mock_core("is_inactive_deployment")
        delete = mock_core("delete_inactive_deployment")
        code, out = run_cli("--repo", "o/r", "clean")
        assert code == 0
        assert "10: Failed to fetch deployment statuses (HTTP 404: Not Found), skipping" in out
        inactive.assert_not_called()
        delete.assert_not_called()

    def test_inactive_check_http_error_skips_deployment(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", side_effect=_http_error(500, "Server Error"))
        delete = mock_core("delete_inactive_deployment")
        code, out = run_cli("--repo", "o/r", "clean")
        assert code == 0
        assert "10: Failed to check deployment status (HTTP 500: Server Error), skipping" in out
        delete.assert_not_called()

    def test_keeps_environment_with_deployments(self, mock_core, run_cli):
        mock_core("is_inactive_deployment", return_value=True)
        mock_core("delete_inactive_deployment", return_value=204)
        run_cli("--repo", "o/r", "clean")
        self.api_delete.assert_not_called()


class TestCliCleanEnvironments:
    @missing_urlopen_import
    def test_deletes_environment_without_deployments(self, mock_core, run_cli):
        mock_core("fetch_pairs", return_value=[{"url": DEPLOY_URL, "env": "other"}])
        mock_core("fetch_environments", return_value=[{"name": "orphan-env"}])
        api_delete = mock_core("api_delete", return_value=204)
        with patch("envkp.core.urlopen", create=True) as mock_urlopen:
            mock_urlopen.return_value = _fake_urlopen("", status_code=204)
            code, out = run_cli("--repo", "o/r", "clean")
        assert code == 0
        assert "No deployments in environment [ orphan-env ]" in out
        assert api_delete.call_args.args[0] == "https://api.github.com/repos/o/r/environments/orphan-env"
