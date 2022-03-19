"""Tests for footing.check module"""
import os
import subprocess

import pytest

import footing.check
import footing.constants
import footing.exceptions


def test_is_git_ssh_path_valid():
    footing.check.is_git_ssh_path('git@github.com:user/template.git')


@pytest.mark.parametrize(
    'invalid_template_path',
    [
        'bad_path',
        'git@github.com:user/template',
        '',
        'abc@def.com:user/template.git',
    ],
)
def test_is_git_ssh_path_invalid(invalid_template_path):
    with pytest.raises(footing.exceptions.InvalidTemplatePathError):
        footing.check.is_git_ssh_path(invalid_template_path)


@pytest.mark.parametrize(
    'revparse_returncode',
    [
        pytest.param(
            255,
            marks=pytest.mark.xfail(raises=footing.exceptions.NotInGitRepoError),
        ),
        0,
    ],
)
def test_in_git_repo(revparse_returncode, mocker):
    """Tests footing.check.not_in_git_repo"""
    revparse_return = subprocess.CompletedProcess([], returncode=revparse_returncode)
    mock_shell = mocker.patch('footing.utils.shell', autospec=True, return_value=revparse_return)

    assert footing.check.in_git_repo() is None

    mock_shell.assert_called_once_with('git rev-parse', stderr=subprocess.DEVNULL, check=False)


@pytest.mark.parametrize(
    'revparse_returncode',
    [
        255,
        pytest.param(
            0,
            marks=pytest.mark.xfail(raises=footing.exceptions.InGitRepoError),
        ),
    ],
)
def test_not_in_git_repo(revparse_returncode, mocker):
    """Tests footing.check.not_in_git_repo"""
    revparse_return = subprocess.CompletedProcess([], returncode=revparse_returncode)
    mock_shell = mocker.patch('footing.utils.shell', autospec=True, return_value=revparse_return)

    assert footing.check.not_in_git_repo() is None

    mock_shell.assert_called_once_with('git rev-parse', stderr=subprocess.DEVNULL, check=False)


@pytest.mark.parametrize(
    'revparse_returncode',
    [
        0,
        pytest.param(
            255,
            marks=pytest.mark.xfail(raises=footing.exceptions.InDirtyRepoError),
        ),
    ],
)
def test_in_clean_repo(revparse_returncode, mocker):
    """Tests footing.check.in_clean_repo"""
    revparse_return = subprocess.CompletedProcess([], returncode=revparse_returncode)
    mock_shell = mocker.patch('footing.utils.shell', autospec=True, return_value=revparse_return)

    assert footing.check.in_clean_repo() is None

    mock_shell.assert_called_once_with('git diff-index --quiet HEAD --', check=False)


@pytest.mark.parametrize(
    'revparse_returncode',
    [
        128,
        pytest.param(
            0,
            marks=pytest.mark.xfail(raises=footing.exceptions.ExistingBranchError),
        ),
    ],
)
def test_not_has_branch(revparse_returncode, mocker):
    """Tests footing.check.not_has_branch"""
    revparse_return = subprocess.CompletedProcess([], returncode=revparse_returncode)
    mock_shell = mocker.patch('footing.utils.shell', autospec=True, return_value=revparse_return)

    assert footing.check.not_has_branch('somebranch') is None

    mock_shell.assert_called_once_with(
        'git rev-parse --verify somebranch',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


@pytest.mark.parametrize(
    'envvar_names, check_envvar_names',
    [
        pytest.param(
            ['v1', 'v2'],
            ['v2', 'v3'],
            marks=pytest.mark.xfail(raises=footing.exceptions.InvalidEnvironmentError),
        ),
        pytest.param(
            [],
            ['v2'],
            marks=pytest.mark.xfail(raises=footing.exceptions.InvalidEnvironmentError),
        ),
        (['v2'], ['v2']),
        (['v1', 'v2'], ['v1', 'v2']),
    ],
)
def test_has_env_vars(envvar_names, check_envvar_names, mocker):
    """Tests footing.check.has_circleci_api_token"""
    mocker.patch.dict(
        os.environ,
        {var_name: 'value' for var_name in envvar_names},
        clear=True,
    )

    assert footing.check.has_env_vars(*check_envvar_names) is None


@pytest.mark.parametrize(
    'footing_file',
    [
        pytest.param(
            'regular_file',
            marks=pytest.mark.xfail(raises=footing.exceptions.InvalidFootingProjectError),
        ),
        footing.constants.FOOTING_CONFIG_FILE,
    ],
)
def test_check_is_footing_project(footing_file, fs):
    """Tests update._check_is_footing_project"""
    fs.CreateFile(footing_file)

    assert footing.check.is_footing_project() is None
