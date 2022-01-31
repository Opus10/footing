.. _installation:


Installation
============

Footing can be installed with::

    pip3 install footing

Most footing functionality requires either a ``GITHUB_API_TOKEN`` or ``GITLAB_API_TOKEN`` environment variable to be set
depending on which git forge is used.

The Github API token is a personal token that you create
by following the `Github Access Token Instructions`_.
This token only requires ``repo`` scope.

.. _Github Access Token Instructions: https://help.github.com/articles/creating-an-access-token-for-command-line-use/

The Gitlab API token is a personal access token created by
following the `Gitlab Access Token Instructions`_.
This token only requires ``read_repository`` scope.

.. _Gitlab Access Token Instructions: https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token

.. note::

    Footing requires a git forge API token for listing available templates, starting new projects, and updating a project
    with a template. However, project templates themselves might have other setup requirements. Consult the documentation
    of templates you want to use for your projects for information about other installation and setup required.
