"""Shared footing utilities."""

import contextlib
import functools
import os
import subprocess

import cookiecutter.config as cc_config
import cookiecutter.generate as cc_generate
import cookiecutter.prompt as cc_prompt
import cookiecutter.repository as cc_repository
import yaml

import footing.constants
import footing.exceptions


def get_repo_path(template):
    """Given a git SSH path (e.g git@github.com:owner/repo.git), return the repo path

    The repo path is in the form of "owner/repo"
    """
    return template[:-4].split(":")[1]


def shell(cmd, check=True, stdin=None, stdout=None, stderr=None):
    """Runs a subprocess shell with check=True by default"""
    return subprocess.run(cmd, shell=True, check=check, stdin=stdin, stdout=stdout, stderr=stderr)


@contextlib.contextmanager
def cd(path):
    """A context manager for changing into a directory"""
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


def read_footing_config():
    """Reads the footing YAML configuration file in the repository"""
    with open(footing.constants.FOOTING_CONFIG_FILE) as footing_config_file:
        return yaml.load(footing_config_file, Loader=yaml.SafeLoader)


def write_footing_config(footing_config, template, version):
    """Writes the footing YAML configuration"""
    with open(footing.constants.FOOTING_CONFIG_FILE, "w") as footing_config_file:
        versioned_config = {
            **footing_config,
            **{"_version": version, "_template": template},
        }
        yaml.dump(versioned_config, footing_config_file, Dumper=yaml.SafeDumper)


def get_cookiecutter_config(template, default_config=None, version=None):
    """Obtains the configuration used for cookiecutter templating

    Args:
        template: Path to the template
        default_config (dict, optional): The default configuration
        version (str, optional): The git SHA or branch to use when
            checking out template. Defaults to latest version

    Returns:
        tuple: The cookiecutter repo directory and the config dict
    """
    default_config = default_config or {}
    config_dict = cc_config.get_user_config()
    repo_dir, _ = cc_repository.determine_repo_dir(
        template=template,
        abbreviations=config_dict["abbreviations"],
        clone_to_dir=config_dict["cookiecutters_dir"],
        checkout=version,
        no_input=True,
    )
    context_file = os.path.join(repo_dir, "cookiecutter.json")
    context = cc_generate.generate_context(
        context_file=context_file,
        default_context={**config_dict["default_context"], **default_config},
    )
    return repo_dir, cc_prompt.prompt_for_config(context)


def set_cmd_env_var(value):
    """Decorator that sets the footing command env var to value"""

    def func_decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            previous_cmd_env_var = os.getenv(footing.constants.FOOTING_ENV_VAR)
            os.environ[footing.constants.FOOTING_ENV_VAR] = value
            try:
                ret_val = function(*args, **kwargs)
            finally:
                if previous_cmd_env_var is None:
                    del os.environ[footing.constants.FOOTING_ENV_VAR]
                else:
                    os.environ[footing.constants.FOOTING_ENV_VAR] = previous_cmd_env_var

            return ret_val

        return wrapper

    return func_decorator
