"""Tests for footing.ls module"""
import os
import subprocess
import urllib

import pytest
import requests
from requests import codes as http_codes

import footing.constants
import footing.exceptions
import footing.forge


@pytest.mark.parametrize(
    "gitlab_api_token",
    [
        "token",
        pytest.param(
            "",
            marks=pytest.mark.xfail(raises=footing.exceptions.InvalidEnvironmentError),
        ),
    ],
)
def test_gitlab_get_client(gitlab_api_token, mocker):
    """Tests footing.forget.Gitlab.get_client()"""
    mocker.patch.dict(os.environ, {"GITLAB_API_TOKEN": gitlab_api_token}, clear=True)

    assert footing.forge.Gitlab().get_client("https://gitlab.com")


def test_gitlab_get_gitlab_url_and_repo_path():
    """Tests footing.forge.Gitlab._get_gitlab_url_and_repo_path"""
    assert footing.forge.Gitlab()._get_gitlab_url_and_repo_path(
        "git@gitlab.com:group/path.git"
    ) == ("https://gitlab.com", "group/path")


@pytest.mark.parametrize(
    "forge, expected_results",
    [
        ("gitlab.com/my/group", ("https://gitlab.com", "my/group")),
        ("gitlab.com/my/group/", ("https://gitlab.com", "my/group")),
        ("http://gitlab.com/my/group", ("http://gitlab.com", "my/group")),
        pytest.param(
            "gitlab.com",
            None,
            marks=pytest.mark.xfail(raises=footing.exceptions.InvalidGitlabGroupError),
        ),
    ],
)
def test_gitlab_get_gitlab_url_and_group(forge, expected_results):
    """Tests footing.forge.Gitlab._get_gitlab_url_and_group"""
    assert footing.forge.Gitlab()._get_gitlab_url_and_group(forge) == expected_results


@pytest.mark.parametrize(
    "http_status",
    [
        http_codes.ok,
        pytest.param(
            http_codes.not_found,
            marks=pytest.mark.xfail(raises=requests.exceptions.HTTPError),
        ),
    ],
)
def test_github_get_latest_template_version_api(http_status, mocker, responses):
    """Tests footing.forge.Github._get_latest_template_version"""
    api = "https://api.github.com/repos/owner/template/commits"
    responses.add(responses.GET, api, json=[{"sha": "v1"}], status=http_status)

    latest = footing.forge.Github()._get_latest_template_version(
        "git@github.com:owner/template.git"
    )
    assert latest == "v1"


@pytest.mark.parametrize(
    "stdout, stderr, expected",
    [
        (b"version\n", b"", "version"),
        (b"version\n", b"stderr_can_be_there_w_stdout", "version"),
        pytest.param(
            b"\n",
            b"stderr_w_no_stdout_is_an_error",
            None,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ],
)
def test_get_latest_template_version_w_ssh(mocker, stdout, stderr, expected):
    """Tests footing.forge._get_latest_template_version_w_ssh"""
    ls_remote_return = subprocess.CompletedProcess([], returncode=0, stdout=stdout, stderr=stderr)
    mock_shell = mocker.patch("footing.utils.shell", autospec=True, return_value=ls_remote_return)

    assert footing.forge._get_latest_template_version_w_ssh("t") == expected
    cmd = "git ls-remote t | grep HEAD | cut -f1"
    mock_shell.assert_called_once_with(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pytest.mark.parametrize(
    "git_ssh_side_effect, git_api_side_effect, expected",
    [
        (["version"], None, "version"),
        (
            subprocess.CalledProcessError(returncode=1, cmd="cmd"),
            ["version"],
            "version",
        ),
        pytest.param(
            subprocess.CalledProcessError(returncode=1, cmd="cmd"),
            requests.exceptions.RequestException,
            None,
            marks=pytest.mark.xfail(raises=footing.exceptions.CheckRunError),
        ),
        pytest.param(
            subprocess.CalledProcessError(returncode=1, cmd="cmd"),
            footing.exceptions.InvalidEnvironmentError,
            None,
            marks=pytest.mark.xfail(raises=footing.exceptions.CheckRunError),
        ),
    ],
)
def test_github_get_latest_template_version(
    mocker, git_ssh_side_effect, git_api_side_effect, expected
):
    mocker.patch(
        "footing.forge._get_latest_template_version_w_ssh",
        autospec=True,
        side_effect=git_ssh_side_effect,
    )
    mocker.patch.object(
        footing.forge.Github,
        "_get_latest_template_version",
        autospec=True,
        side_effect=git_api_side_effect,
    )

    version = footing.forge.Github().get_latest_template_version("template")
    assert version == expected


@pytest.mark.parametrize(
    "root, expected_client_cls",
    [
        ("github.com/user", footing.forge.Github),
        ("gitlab.com/user", footing.forge.Gitlab),
        pytest.param(
            "invalid",
            None,
            marks=pytest.mark.xfail(raises=footing.exceptions.InvalidForgeError),
        ),
    ],
)
def test_from_path(root, expected_client_cls):
    client = footing.forge.from_path(root)
    assert client.__class__ == expected_client_cls


@pytest.mark.parametrize(
    "headers, expected_links",
    [
        ({"no_link_keys": "value"}, {}),
        (
            {"link": '<https://url.com>; rel="next", <https://url2.com>; rel="last"'},
            {"next": "https://url.com", "last": "https://url2.com"},
        ),
    ],
)
def test_github_parse_link_header(headers, expected_links):
    """Tests footing.forge.Github._parse_link_header"""
    assert footing.forge.Github()._parse_link_header(headers) == expected_links


def test_github_code_search_single_page(mocker, responses):
    """Tests ls.ls for a single page of responses"""
    response_content = {
        "items": [
            {
                "repository": {
                    "full_name": "repo/repo1",
                },
            },
            {
                "repository": {
                    "full_name": "repo/repo2",
                },
            },
        ],
    }
    responses.add(
        responses.GET,
        "https://api.github.com/search/code",
        status=requests.codes.ok,
        json=response_content,
    )

    query = 'user:user {} in:path "template_path" in:file'.format(
        footing.constants.FOOTING_CONFIG_FILE
    )
    repos = footing.forge.Github()._code_search(query)

    assert repos == {
        "git@github.com:repo/repo1.git": {"full_name": "repo/repo1"},
        "git@github.com:repo/repo2.git": {"full_name": "repo/repo2"},
    }
    assert len(responses.calls) == 1
    url = urllib.parse.urlparse(responses.calls[0].request.url)
    parsed_query = urllib.parse.parse_qs(url.query)
    assert parsed_query == {
        "per_page": ["100"],
        "q": [query],
    }


def test_github_code_search_multiple_pages(mocker, responses):
    """Tests footing.forge.Github._code_search for a single page of responses"""
    response_content1 = {
        "items": [
            {
                "repository": {
                    "full_name": "repo/repo1",
                },
            },
            {
                "repository": {
                    "full_name": "repo/repo2",
                },
            },
        ],
    }
    response_link_header1 = {
        "link": '<https://next_url.com>; rel="next", <https://next_url2.com>; rel="last"',
    }
    response_content2 = {
        "items": [
            {
                "repository": {
                    "full_name": "repo/repo3",
                },
            },
            {
                "repository": {
                    "full_name": "repo/repo4",
                },
            },
        ],
    }
    responses.add(
        responses.GET,
        "https://api.github.com/search/code",
        status=requests.codes.ok,
        json=response_content1,
        adding_headers=response_link_header1,
    )
    responses.add(
        responses.GET,
        "https://next_url.com",
        status=requests.codes.ok,
        json=response_content2,
    )

    repos = footing.forge.Github()._code_search("query")

    assert repos == {
        "git@github.com:repo/repo1.git": {"full_name": "repo/repo1"},
        "git@github.com:repo/repo2.git": {"full_name": "repo/repo2"},
        "git@github.com:repo/repo3.git": {"full_name": "repo/repo3"},
        "git@github.com:repo/repo4.git": {"full_name": "repo/repo4"},
    }


@pytest.mark.parametrize(
    "ssh_path, expected_name",
    [
        ("git@github.com:user/template.git", "template"),
        ("git@github.com:user/foo-bar.git", "foo-bar"),
        ("git@github.com:user/foo_bar1.git", "foo_bar1"),
    ],
)
def test_get_name_from_ssh_path(ssh_path, expected_name):
    assert footing.forge.get_name_from_ssh_path(ssh_path) == expected_name


def test_github_code_search_invalid_root(mocker, responses):
    """Tests footing.forge.Github._code_search when the root is invalid"""
    responses.add(
        responses.GET,
        "https://api.github.com/search/code",
        status=requests.codes.unprocessable_entity,
        json={},
    )

    query = 'user:user {} in:path "template_path" in:file'.format(
        footing.constants.FOOTING_CONFIG_FILE
    )
    with pytest.raises(footing.exceptions.InvalidForgeError):
        footing.forge.Github()._code_search("invalid", query)
