"""
footing.update
~~~~~~~~~~~~~~

Updates a footing project with the latest template
"""
import json
import os
import shutil
import subprocess
import tempfile
import textwrap

import cookiecutter.main as cc_main
import cookiecutter.vcs as cc_vcs

import footing.check
import footing.constants
import footing.forge
import footing.utils


def _cookiecutter_configs_have_changed(template, old_version, new_version):
    """Given an old version and new version, check if the cookiecutter.json files have changed

    When the cookiecutter.json files change, it means the user will need to be prompted for
    new context

    Args:
        template (str): The git path to the template
        old_version (str): The git SHA of the old version
        new_version (str): The git SHA of the new version

    Returns:
        bool: True if the cookiecutter.json files have been changed in the old and new versions
    """
    with tempfile.TemporaryDirectory() as clone_dir:
        repo_dir = cc_vcs.clone(template, old_version, clone_dir)
        old_config = json.load(open(os.path.join(repo_dir, 'cookiecutter.json')))
        subprocess.check_call(
            'git checkout %s' % new_version,
            cwd=repo_dir,
            shell=True,
            stderr=subprocess.PIPE,
        )
        new_config = json.load(open(os.path.join(repo_dir, 'cookiecutter.json')))

    return old_config != new_config


def _apply_template(template, target, *, checkout, extra_context):
    """Apply a template to a temporary directory and then copy results to target."""
    with tempfile.TemporaryDirectory() as tempdir:
        repo_dir = cc_main.cookiecutter(
            template,
            checkout=checkout,
            no_input=True,
            output_dir=tempdir,
            extra_context=extra_context,
        )
        for item in os.listdir(repo_dir):
            src = os.path.join(repo_dir, item)
            dst = os.path.join(target, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.copy2(src, dst)


def _get_latest_template_version(template):
    """Obtains the latest template version from the appropriate git forge"""
    client = footing.forge.from_path(template)
    return client.get_latest_template_version(template)


@footing.utils.set_cmd_env_var('update')
def up_to_date(version=None):
    """Checks if a footing project is up to date with the repo

    Note that the `footing.constants.FOOTING_ENV_VAR` is set to 'update' for the duration of this
    function.

    Args:
        version (str, optional): Update against this git SHA or branch of the template

    Returns:
        boolean: True if up to date with ``version`` (or latest version), False otherwise

    Raises:
        `NotInGitRepoError`: When running outside of a git repo
        `InvalidFootingProjectError`: When not inside a valid footing repository
    """
    footing.check.in_git_repo()
    footing.check.is_footing_project()

    footing_config = footing.utils.read_footing_config()
    old_template_version = footing_config['_version']
    new_template_version = version or _get_latest_template_version(footing_config['_template'])

    return new_template_version == old_template_version


def _needs_new_cc_config_for_update(old_template, old_version, new_template, new_version):
    """
    Given two templates and their respective versions, return True if a new cookiecutter
    config needs to be obtained from the user
    """
    if old_template != new_template:
        return True
    else:
        return _cookiecutter_configs_have_changed(new_template, old_version, new_version)


@footing.utils.set_cmd_env_var('update')
def update(
    old_template=None,
    old_version=None,
    new_template=None,
    new_version=None,
    enter_parameters=False,
):
    """Updates the footing project to the latest template

    Proceeeds in the following steps:

    1. Ensure we are inside the project repository
    2. Obtain the latest version of the package template
    3. If the package is up to date with the latest template, return
    4. If not, create an empty template branch with a new copy of the old template
    5. Create an update branch from HEAD and merge in the new template copy
    6. Create a new copy of the new template and merge into the empty template branch
    7. Merge the updated empty template branch into the update branch
    8. Ensure footing.yaml reflects what is in the template branch
    9. Remove the empty template branch

    Note that the `footing.constants.FOOTING_ENV_VAR` is set to 'update' for the
    duration of this function.

    Two branches will be created during the update process, one named
    ``_footing_update`` and one named ``_footing_update_temp``. At the end of
    the process, ``_footing_update_temp`` will be removed automatically. The
    work will be left in ``_footing_update`` in an uncommitted state for
    review. The update will fail early if either of these branches exist
    before the process starts.

    Args:
        old_template (str, default=None): The old template from which to update. Defaults
            to the template in footing.yaml
        old_version (str, default=None): The old version of the template. Defaults to
            the version in footing.yaml
        new_template (str, default=None): The new template for updating. Defaults to the
            template in footing.yaml
        new_version (str, default=None): The new version of the new template to update.
            Defaults to the latest version of the new template
        enter_parameters (bool, default=False): Force entering template parameters for the project

    Raises:
        `NotInGitRepoError`: When not inside of a git repository
        `InvalidFootingProjectError`: When not inside a valid footing repository
        `InDirtyRepoError`: When an update is triggered while the repo is in a dirty state
        `ExistingBranchError`: When an update is triggered and there is an existing
            update branch

    Returns:
        boolean: True if update was performed or False if template was already up to date
    """
    update_branch = footing.constants.UPDATE_BRANCH_NAME
    temp_update_branch = footing.constants.TEMP_UPDATE_BRANCH_NAME

    footing.check.in_git_repo()
    footing.check.in_clean_repo()
    footing.check.is_footing_project()
    footing.check.not_has_branch(update_branch)
    footing.check.not_has_branch(temp_update_branch)

    footing_config = footing.utils.read_footing_config()
    old_template = old_template or footing_config['_template']
    new_template = new_template or footing_config['_template']
    old_version = old_version or footing_config['_version']
    new_version = new_version or _get_latest_template_version(new_template)

    if new_template == old_template and new_version == old_version and not enter_parameters:
        print('No updates have happened to the template, so no files were updated')
        return False

    print('Creating branch {} for processing the update'.format(update_branch))
    footing.utils.shell('git checkout -b {}'.format(update_branch), stderr=subprocess.DEVNULL)

    print('Creating temporary working branch {}'.format(temp_update_branch))
    footing.utils.shell(
        'git checkout --orphan {}'.format(temp_update_branch),
        stderr=subprocess.DEVNULL,
    )
    footing.utils.shell('git rm -rf .', stdout=subprocess.DEVNULL)
    _apply_template(old_template, '.', checkout=old_version, extra_context=footing_config)
    footing.utils.shell('git add .')
    footing.utils.shell(
        'git commit --no-verify -m "Initialize template from version {}"'.format(old_version),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print('Merge old template history into update branch.')
    footing.utils.shell('git checkout {}'.format(update_branch), stderr=subprocess.DEVNULL)
    footing.utils.shell(
        'git merge -s ours --no-edit --allow-unrelated-histories {}'.format(temp_update_branch),
        stderr=subprocess.DEVNULL,
    )

    print('Update template in temporary branch.')
    footing.utils.shell('git checkout {}'.format(temp_update_branch), stderr=subprocess.DEVNULL)
    footing.utils.shell('git rm -rf .', stdout=subprocess.DEVNULL)

    # If the cookiecutter.json files have changed or the templates have changed,
    # the user will need to re-enter the cookiecutter config
    needs_new_cc_config = _needs_new_cc_config_for_update(
        old_template, old_version, new_template, new_version
    )
    if needs_new_cc_config:
        if old_template != new_template:
            cc_config_input_msg = (
                'You will be prompted for the parameters of the new template.'
                ' Please read the docs at https://github.com/{} before entering parameters.'
                ' Press enter to continue'
            ).format(footing.utils.get_repo_path(new_template))
        else:
            cc_config_input_msg = (
                'A new template variable has been defined in the updated template.'
                ' You will be prompted to enter all of the variables again. Variables'
                ' already configured in your project will have their values set as'
                ' defaults. Press enter to continue'
            )

        input(cc_config_input_msg)

    # Even if there is no detected need to re-enter the cookiecutter config, the user
    # can still re-enter config parameters with the "enter_parameters" flag
    if needs_new_cc_config or enter_parameters:
        _, footing_config = footing.utils.get_cookiecutter_config(
            new_template, default_config=footing_config, version=new_version
        )

    _apply_template(new_template, '.', checkout=new_version, extra_context=footing_config)
    footing.utils.write_footing_config(footing_config, new_template, new_version)

    footing.utils.shell('git add .')
    footing.utils.shell(
        'git commit --no-verify -m "Update template to version {}"'.format(new_version),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print('Merge updated template into update branch.')
    footing.utils.shell('git checkout {}'.format(update_branch), stderr=subprocess.DEVNULL)
    footing.utils.shell(
        'git merge --no-commit {}'.format(temp_update_branch),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # The footing.yaml file should always reflect what is in the new template
    footing.utils.shell(
        'git checkout --theirs {}'.format(footing.constants.FOOTING_CONFIG_FILE),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print('Remove temporary template branch {}'.format(temp_update_branch))
    footing.utils.shell(
        'git branch -D {}'.format(temp_update_branch),
        stdout=subprocess.DEVNULL,
    )

    print(
        textwrap.dedent(
            """\
        Updating complete!

        Please review the changes with "git status" for any errors or
        conflicts. Once you are satisfied with the changes, add, commit,
        push, and open a PR with the branch {}
    """
        ).format(update_branch)
    )
    return True
