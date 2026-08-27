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


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------

class TestGetVersion:
    def test_returns_version_string(self):
        assert get_version() == __version__

    def test_version_is_semver_like(self):
        parts = get_version().split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()


# ---------------------------------------------------------------------------
# cli_precheck
# ---------------------------------------------------------------------------

class TestCliPrecheck:
    def test_valid_repo_and_token(self, capsys):
        assert cli_precheck(repo="owner/repo", token="ghp_abc123") is True

    def test_repo_missing_slash(self, capsys):
        assert cli_precheck(repo="invalid-repo", token="ghp_abc123") is False
        captured = capsys.readouterr()
        assert "format invalid" in captured.out

    def test_repo_too_many_slashes(self, capsys):
        assert cli_precheck(repo="a/b/c", token="ghp_abc123") is False
        captured = capsys.readouterr()
        assert "format invalid" in captured.out

    def test_token_none(self, capsys):
        assert cli_precheck(repo="owner/repo", token=None) is False
        captured = capsys.readouterr()
        assert "GH_TOKEN" in captured.out

    def test_empty_repo(self, capsys):
        assert cli_precheck(repo="", token="tok") is False

    def test_single_segment_repo(self, capsys):
        assert cli_precheck(repo="justrepo", token="tok") is False


# ---------------------------------------------------------------------------
# get_deployments_by_env  (pure function – no mocking needed)
# ---------------------------------------------------------------------------

class TestGetDeploymentsByEnv:
    SAMPLE_MAPPINGS = [
        {"url": "https://api.github.com/repos/o/r/deployments/1/statuses", "env": "production"},
        {"url": "https://api.github.com/repos/o/r/deployments/2/statuses", "env": "staging"},
        {"url": "https://api.github.com/repos/o/r/deployments/3/statuses", "env": "production"},
        {"url": "https://api.github.com/repos/o/r/deployments/4/statuses", "env": "pr-42"},
    ]

    def test_filters_production(self):
        result = get_deployments_by_env(self.SAMPLE_MAPPINGS, "production")
        assert len(result) == 2
        assert all("production" not in url for url in result) or True  # URLs don't contain env name
        assert result[0].endswith("deployments/1/statuses")
        assert result[1].endswith("deployments/3/statuses")

    def test_filters_staging(self):
        result = get_deployments_by_env(self.SAMPLE_MAPPINGS, "staging")
        assert len(result) == 1
        assert result[0].endswith("deployments/2/statuses")

    def test_returns_empty_for_nonexistent_env(self):
        result = get_deployments_by_env(self.SAMPLE_MAPPINGS, "does-not-exist")
        assert result == []

    def test_empty_mappings(self):
        assert get_deployments_by_env([], "production") == []


# ---------------------------------------------------------------------------
# is_pagenated
# ---------------------------------------------------------------------------

class TestIsPagenated:
    def _make_resp(self, headers):
        resp = MagicMock()
        resp.getheaders.return_value = headers
        return resp

    def test_paginated_when_link_header_present(self):
        resp = self._make_resp([("Link", '<...>; rel="next"'), ("Content-Type", "application/json")])
        assert is_pagenated(resp) is True

    def test_not_paginated_when_no_link_header(self):
        resp = self._make_resp([("Content-Type", "application/json")])
        assert is_pagenated(resp) is False

    def test_empty_headers(self):
        resp = self._make_resp([])
        assert is_pagenated(resp) is False


# ---------------------------------------------------------------------------
# Helper: build a fake urlopen context manager
# ---------------------------------------------------------------------------

def _fake_urlopen(body, status_code=200, headers=None):
    """Return a context-manager mock that behaves like urlopen(...)."""
    if headers is None:
        headers = [("Content-Type", "application/json")]
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.getcode.return_value = status_code
    resp.getheaders.return_value = headers
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# fetch_pairs
# ---------------------------------------------------------------------------

class TestFetchPairs:
    HEADER = {"authorization": "token test", "accept": "application/json"}
    DEPLOYMENTS = [
        {"statuses_url": "https://api.github.com/repos/o/r/deployments/1/statuses", "environment": "prod"},
        {"statuses_url": "https://api.github.com/repos/o/r/deployments/2/statuses", "environment": "staging"},
    ]

    @patch("envkp.core.urlopen")
    def test_returns_pairs_no_pagination(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(
            self.DEPLOYMENTS,
            headers=[("Content-Type", "application/json")],
        )
        pairs = fetch_pairs(repo="o/r", reqheader=self.HEADER)
        assert len(pairs) == 2
        assert pairs[0]["env"] == "prod"
        assert pairs[1]["url"].endswith("deployments/2/statuses")

    @patch("envkp.core.urlopen")
    def test_handles_pagination(self, mock_urlopen):
        page1_resp = _fake_urlopen(
            self.DEPLOYMENTS,
            headers=[("Content-Type", "application/json"), ("Link", '<...>; rel="next"')],
        )
        page2_data = [
            {"statuses_url": "https://api.github.com/repos/o/r/deployments/3/statuses", "environment": "dev"},
        ]
        page2_resp = _fake_urlopen(page2_data)

        mock_urlopen.side_effect = [page1_resp, page2_resp]
        pairs = fetch_pairs(repo="o/r", reqheader=self.HEADER)
        assert len(pairs) == 3
        assert pairs[2]["env"] == "dev"

    @patch("envkp.core.urlopen")
    def test_empty_deployments(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(
            [],
            headers=[("Content-Type", "application/json")],
        )
        pairs = fetch_pairs(repo="o/r", reqheader=self.HEADER)
        assert pairs == []


# ---------------------------------------------------------------------------
# fetch_environments
# ---------------------------------------------------------------------------

class TestFetchEnvironments:
    HEADER = {"authorization": "token test", "accept": "application/json"}

    @patch("envkp.core.urlopen")
    def test_returns_environments(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(
            {"environments": [{"name": "production"}, {"name": "staging"}]}
        )
        envs = fetch_environments(repo="o/r", reqheader=self.HEADER)
        assert len(envs) == 2
        assert envs[0]["name"] == "production"

    @patch("envkp.core.urlopen")
    def test_no_environments(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen({"environments": []})
        envs = fetch_environments(repo="o/r", reqheader=self.HEADER)
        assert envs == []


# ---------------------------------------------------------------------------
# get_deployment_statuses
# ---------------------------------------------------------------------------

class TestGetDeploymentStatuses:
    HEADER = {"authorization": "token test", "accept": "application/json"}

    @patch("envkp.core.urlopen")
    def test_returns_id_state_tuples(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen([
            {"id": 100, "state": "success"},
            {"id": 101, "state": "inactive"},
        ])
        result = get_deployment_statuses(
            status_url="https://api.github.com/repos/o/r/deployments/1/statuses",
            reqheader=self.HEADER,
        )
        assert result == [(100, "success"), (101, "inactive")]

    @patch("envkp.core.urlopen")
    def test_empty_statuses(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen([])
        result = get_deployment_statuses(
            status_url="https://api.github.com/repos/o/r/deployments/1/statuses",
            reqheader=self.HEADER,
        )
        assert result == []


# ---------------------------------------------------------------------------
# is_inactive_deployment
# ---------------------------------------------------------------------------

class TestIsInactiveDeployment:
    HEADER = {"authorization": "token test", "accept": "application/json"}

    @patch("envkp.core.get_deployment_statuses")
    def test_inactive_when_status_is_inactive(self, mock_statuses):
        mock_statuses.return_value = [(1, "inactive")]
        assert is_inactive_deployment(d="url", reqheader=self.HEADER) is True

    @patch("envkp.core.get_deployment_statuses")
    def test_active_when_status_is_success(self, mock_statuses):
        mock_statuses.return_value = [(1, "success")]
        assert is_inactive_deployment(d="url", reqheader=self.HEADER) is False

    @patch("envkp.core.get_deployment_statuses")
    def test_inactive_when_only_in_progress(self, mock_statuses):
        mock_statuses.return_value = [(1, "in_progress")]
        assert is_inactive_deployment(d="url", reqheader=self.HEADER) is True

    @patch("envkp.core.get_deployment_statuses")
    def test_inactive_when_failure(self, mock_statuses):
        mock_statuses.return_value = [(1, "failure")]
        assert is_inactive_deployment(d="url", reqheader=self.HEADER) is True

    @patch("envkp.core.get_deployment_statuses")
    def test_inactive_when_inactive_and_success_both_present(self, mock_statuses):
        mock_statuses.return_value = [(1, "inactive"), (2, "success")]
        assert is_inactive_deployment(d="url", reqheader=self.HEADER) is True

    @patch("envkp.core.get_deployment_statuses")
    def test_active_when_only_success(self, mock_statuses):
        mock_statuses.return_value = [(1, "success"), (2, "success")]
        assert is_inactive_deployment(d="url", reqheader=self.HEADER) is False

    @patch("envkp.core.get_deployment_statuses")
    def test_inactive_when_empty_statuses(self, mock_statuses):
        mock_statuses.return_value = []
        assert is_inactive_deployment(d="url", reqheader=self.HEADER) is True


# ---------------------------------------------------------------------------
# delete_inactive_deployment
# ---------------------------------------------------------------------------

class TestDeleteInactiveDeployment:
    HEADER = {"authorization": "token test", "accept": "application/json"}

    @patch("envkp.core.urlopen")
    def test_returns_204_on_success(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(body="", status_code=204)
        code = delete_inactive_deployment(
            deployment_id="123", gh_reponame="o/r", reqheader=self.HEADER
        )
        assert code == 204

    @patch("envkp.core.urlopen")
    def test_returns_non_204_on_error(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen(body="", status_code=422)
        code = delete_inactive_deployment(
            deployment_id="123", gh_reponame="o/r", reqheader=self.HEADER
        )
        assert code == 422


# ---------------------------------------------------------------------------
# fetch_cli_args
# ---------------------------------------------------------------------------

class TestFetchCliArgs:
    def test_clean_subcommand(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "owner/repo", "clean"])
        parser, args = fetch_cli_args()
        assert args.subcommand == "clean"
        assert args.repo == "owner/repo"

    def test_seek_subcommand(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "owner/repo", "seek"])
        parser, args = fetch_cli_args()
        assert args.subcommand == "seek"

    def test_version_subcommand(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "version"])
        parser, args = fetch_cli_args()
        assert args.subcommand == "version"

    def test_help_subcommand(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "help"])
        parser, args = fetch_cli_args()
        assert args.subcommand == "help"

    def test_no_subcommand(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp"])
        parser, args = fetch_cli_args()
        assert args.subcommand is None

    def test_clean_with_force(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean", "--force"])
        parser, args = fetch_cli_args()
        assert args.force is True

    def test_seek_with_verbose(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "seek", "--verbose"])
        parser, args = fetch_cli_args()
        assert args.verbose is True


# ---------------------------------------------------------------------------
# cli() – integration-style tests
# ---------------------------------------------------------------------------

class TestCli:
    """Tests for the cli() entry point covering all branches."""

    def test_no_subcommand_prints_help_and_exits(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp"])
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 1

    def test_help_subcommand_exits_zero(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "help"])
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0

    def test_version_subcommand_prints_version(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["envkp", "version"])
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert __version__ in captured.out

    def test_missing_repo_exits_1(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "clean"])
        monkeypatch.delenv("GH_REPONAME", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 1

    def test_invalid_repo_format_exits_1(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "badformat", "clean"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 1

    def test_missing_token_exits_1(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean"])
        monkeypatch.delenv("GH_TOKEN", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 1

    # -- fetch_pairs raises HTTPError --

    @patch("envkp.core.fetch_pairs")
    def test_http_error_during_fetch_pairs_exits_1(self, mock_fp, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        mock_fp.side_effect = HTTPError(
            url="https://api.github.com", code=404, msg="Not Found", hdrs=None, fp=None
        )
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 1

    # -- empty pairs → early exit --

    @patch("envkp.core.fetch_pairs")
    def test_empty_pairs_exits_0(self, mock_fp, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        mock_fp.return_value = []
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No environment found" in captured.out

    # -- seek subcommand full flow --

    @patch("envkp.core.is_inactive_deployment")
    @patch("envkp.core.fetch_environments")
    @patch("envkp.core.fetch_pairs")
    def test_seek_prints_deployment_urls(self, mock_fp, mock_fe, mock_inactive, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "seek"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        mock_fp.return_value = [
            {"url": "https://api.github.com/repos/o/r/deployments/1/statuses", "env": "prod"},
        ]
        mock_fe.return_value = [{"name": "prod"}]
        mock_inactive.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "deployments/1/statuses" in captured.out
        assert "is_inactive: True" in captured.out

    # -- clean subcommand: inactive deployment → delete succeeds (204) --

    @patch("envkp.core.delete_inactive_deployment")
    @patch("envkp.core.is_inactive_deployment")
    @patch("envkp.core.get_deployment_statuses")
    @patch("envkp.core.fetch_environments")
    @patch("envkp.core.fetch_pairs")
    def test_clean_deletes_inactive_deployment(
        self, mock_fp, mock_fe, mock_statuses, mock_inactive, mock_delete, monkeypatch, capsys
    ):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        mock_fp.return_value = [
            {"url": "https://api.github.com/repos/o/r/deployments/10/statuses", "env": "staging"},
        ]
        mock_fe.return_value = [{"name": "staging"}]
        mock_statuses.return_value = [(1, "inactive")]
        mock_inactive.return_value = True
        mock_delete.return_value = 204

        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Done, 204" in captured.out
        mock_delete.assert_called_once()

    # -- clean subcommand: inactive deployment → delete fails (non-204) --

    @patch("envkp.core.delete_inactive_deployment")
    @patch("envkp.core.is_inactive_deployment")
    @patch("envkp.core.get_deployment_statuses")
    @patch("envkp.core.fetch_environments")
    @patch("envkp.core.fetch_pairs")
    def test_clean_delete_error(
        self, mock_fp, mock_fe, mock_statuses, mock_inactive, mock_delete, monkeypatch, capsys
    ):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        mock_fp.return_value = [
            {"url": "https://api.github.com/repos/o/r/deployments/10/statuses", "env": "staging"},
        ]
        mock_fe.return_value = [{"name": "staging"}]
        mock_statuses.return_value = [(1, "inactive")]
        mock_inactive.return_value = True
        mock_delete.return_value = 422

        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Error" in captured.out

    # -- clean subcommand: active deployment → skip --

    @patch("envkp.core.is_inactive_deployment")
    @patch("envkp.core.get_deployment_statuses")
    @patch("envkp.core.fetch_environments")
    @patch("envkp.core.fetch_pairs")
    def test_clean_skips_active_deployment(
        self, mock_fp, mock_fe, mock_statuses, mock_inactive, monkeypatch, capsys
    ):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        mock_fp.return_value = [
            {"url": "https://api.github.com/repos/o/r/deployments/10/statuses", "env": "staging"},
        ]
        mock_fe.return_value = [{"name": "staging"}]
        mock_statuses.return_value = [(1, "success")]
        mock_inactive.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "nothing to do" in captured.out

    # -- clean subcommand: environment with no deployments → delete env (204) --

    @patch("envkp.core.urlopen")
    @patch("envkp.core.fetch_environments")
    @patch("envkp.core.fetch_pairs")
    def test_clean_deletes_empty_environment(self, mock_fp, mock_fe, mock_urlopen, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        # pairs exist for a *different* env, so "orphan-env" has zero deployments
        mock_fp.return_value = [
            {"url": "https://api.github.com/repos/o/r/deployments/1/statuses", "env": "other"},
        ]
        mock_fe.return_value = [{"name": "orphan-env"}]
        mock_urlopen.return_value = _fake_urlopen(body="", status_code=204)

        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No deployments in environment" in captured.out
        assert "Done, 204" in captured.out

    # -- clean subcommand: delete environment fails (non-204) --

    @patch("envkp.core.urlopen")
    @patch("envkp.core.fetch_environments")
    @patch("envkp.core.fetch_pairs")
    def test_clean_delete_env_error(self, mock_fp, mock_fe, mock_urlopen, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["envkp", "--repo", "o/r", "clean"])
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        mock_fp.return_value = [
            {"url": "https://api.github.com/repos/o/r/deployments/1/statuses", "env": "other"},
        ]
        mock_fe.return_value = [{"name": "orphan-env"}]
        mock_urlopen.return_value = _fake_urlopen(body="", status_code=500)

        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Error" in captured.out

    # -- GH_REPONAME env var overrides --repo flag --

    @patch("envkp.core.fetch_pairs")
    def test_env_var_repo_used_when_flag_missing(self, mock_fp, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["envkp", "clean"])
        monkeypatch.setenv("GH_REPONAME", "env/repo")
        monkeypatch.setenv("GH_TOKEN", "fake-token")
        mock_fp.return_value = []
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "env/repo" in captured.out
