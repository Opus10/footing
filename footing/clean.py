"""Functions for cleaning up temporary resources used by footing."""

import subprocess

import footing.check
import footing.constants
import footing.exceptions
import footing.utils


def _get_current_branch():
    """Determine the current git branch"""
    result = footing.utils.shell("git rev-parse --abbrev-ref HEAD", stdout=subprocess.PIPE)
    return result.stdout.decode("utf8").strip()


def clean() -> None:
    """Cleans up temporary resources

    Tries to clean up:

    1. The temporary update branch used during ``footing update``
    2. The primary update branch used during ``footing update``
    """
    footing.check.in_git_repo()

    current_branch = _get_current_branch()
    update_branch = footing.constants.UPDATE_BRANCH_NAME
    temp_update_branch = footing.constants.TEMP_UPDATE_BRANCH_NAME

    if current_branch in (update_branch, temp_update_branch):
        err_msg = (
            'You must change from the "{}" branch since it will be deleted during cleanup'
        ).format(current_branch)
        raise footing.exceptions.InvalidCurrentBranchError(err_msg)

    if footing.check._has_branch(update_branch):
        footing.utils.shell("git branch -D {}".format(update_branch))
    if footing.check._has_branch(temp_update_branch):
        footing.utils.shell("git branch -D {}".format(temp_update_branch))
