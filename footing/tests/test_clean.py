from unittest import mock

import pytest

import footing.clean
import footing.exceptions


@pytest.mark.parametrize(
    'update_branch_exists, temp_update_branch_exists, expected_shell_cmds',
    [
        (False, False, []),
        (True, False, [mock.call('git branch -D _footing_update')]),
        (False, True, [mock.call('git branch -D _footing_update_temp')]),
        (
            True,
            True,
            [
                mock.call('git branch -D _footing_update'),
                mock.call('git branch -D _footing_update_temp'),
            ],
        ),
    ],
)
def test_clean(
    update_branch_exists,
    temp_update_branch_exists,
    expected_shell_cmds,
    mocker,
):
    """Tests footing.clean.clean"""

    def branch_exists_side_effect(branch_name):
        """A side effect to use when mocking out the function that checks if a branch exists"""
        if branch_name == footing.constants.UPDATE_BRANCH_NAME:
            return update_branch_exists
        elif branch_name == footing.constants.TEMP_UPDATE_BRANCH_NAME:
            return temp_update_branch_exists
        else:
            raise AssertionError

    mocker.patch('footing.clean._get_current_branch', return_value='current_branch')
    mocker.patch('footing.check.in_git_repo')
    mocker.patch(
        'footing.check._has_branch',
        autospec=True,
        side_effect=branch_exists_side_effect,
    )
    mock_shell = mocker.patch('footing.utils.shell', autospec=True)
    footing.clean.clean()
    assert mock_shell.call_args_list == expected_shell_cmds


def test_get_current_branch():
    """Verifies that the "_get_current_branch" function returns non-empty data

    This ensures that the proper git call is made and that output is parsed properly"""
    assert footing.clean._get_current_branch()


def test_clean_bad_current_branch(mocker):
    """Tests footing.clean.clean when on a branch that will be deleted"""
    mocker.patch('footing.check.in_git_repo')
    mocker.patch(
        'footing.clean._get_current_branch',
        return_value=footing.constants.UPDATE_BRANCH_NAME,
    )

    with pytest.raises(footing.exceptions.InvalidCurrentBranchError):
        footing.clean.clean()
