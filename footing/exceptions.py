"""Footing exceptions."""


class Error(Exception):
    """The top-level error for footing"""


class InGitRepoError(Error):
    """Thrown when running inside of a git repository"""


class NotInGitRepoError(Error):
    """Thrown when not running inside of a git repo"""


class InDirtyRepoError(Error):
    """Thrown when running in a dirty git repo"""


class InvalidFootingProjectError(Error):
    """Thrown when the repository was not created with footing"""


class NotUpToDateWithTemplateError(Error):
    """Thrown when a footing project is not up to date with the template"""


class CheckRunError(Error):
    """When running ``footing update --check`` errors"""


class InvalidEnvironmentError(Error):
    """Thrown when required environment variables are not set"""


class InvalidForgeError(Error):
    """An invalid forge was passed to ls."""


class InvalidTemplatePathError(Error):
    """Thrown when a template path is not a Github SSH path"""


class ExistingBranchError(Error):
    """Thrown when a specifically named branch exists or doesn't exist as expected."""


class InvalidCurrentBranchError(Error):
    """Thrown when a command cannot run because of the current git branch"""


class InvalidGitlabGroupError(Error):
    """Thrown when an invalid Gitlab group is provided"""
