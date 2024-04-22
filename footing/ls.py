"""Lists all footing templates and projects spun up with those templates."""

from __future__ import annotations

import footing.forge
import footing.utils


@footing.utils.set_cmd_env_var("ls")
def ls(forge: str, template: str | None = None) -> dict[str, str]:
    """Lists all templates under a root path or list all projects spun up under
    a root path and a template path.

    The ``root`` path must be either a Github organization/user (e.g. github.com/organization)
    or a Gitlab group (e.g. gitlab.com/my/group).

    Note that the `footing.constants.FOOTING_ENV_VAR` is set to 'ls' for the duration of this
    function.

    Args:
        forge: A root git storage path.  For example, a Github organization
            (github.com/Organization) or a gitlab group (gitlab.com/my/group).
        template: An optional template path. If provided, the
            returned values are projects under ``root`` created using the template.

    Returns:
        xA dictionary of repository information keyed on the url.

    Raises:
        `InvalidForgeError`: When ``forge`` is invalid
    """
    client = footing.forge.from_path(forge)
    return client.ls(forge, template)
