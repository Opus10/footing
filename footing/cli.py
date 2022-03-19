"""
The footing CLI contains commands for setting up, listing, and updating projects.

Commands
~~~~~~~~

* ``footing setup`` - Sets up a new project
* ``footing ls`` - Lists all templates and projects created with those templates
* ``footing update`` - Updates the project to the latest template version
* ``footing clean`` - Cleans up any temporary resources used by footing
* ``footing switch`` - Switch a project to a different template
"""
import click
import pkg_resources

import footing
import footing.clean
import footing.exceptions
import footing.ls
import footing.setup
import footing.update


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', is_flag=True, help='Show version')
def main(ctx, version):
    if version:
        print('footing {}'.format(pkg_resources.get_distribution('footing').version))
    elif not ctx.invoked_subcommand:
        print(ctx.get_help())


@main.command()
@click.argument('template', nargs=1, required=True)
@click.option(
    '-v',
    '--version',
    default=None,
    help='Git SHA or branch of template to use for creation',
)
def setup(template, version):
    """
    Setup new project. Takes a git path to the template as returned
    by "footing ls". In order to start a project from a
    particular version (instead of the latest), use the "-v" option.
    """
    footing.setup.setup(template, version=version)


@main.command()
@click.option('-c', '--check', is_flag=True, help='Check to see if up to date')
@click.option(
    '-e',
    '--enter-parameters',
    is_flag=True,
    help='Enter template parameters on update',
)
@click.option(
    '-v',
    '--version',
    default=None,
    help='Git SHA or branch of template to use for update',
)
def update(check, enter_parameters, version):
    """
    Update package with latest template. Must be inside of the project
    folder to run.

    Using "-e" will prompt for re-entering the template parameters again
    even if the project is up to date.

    Use "-v" to update to a particular version of a template.

    Using "-c" will perform a check that the project is up to date
    with the latest version of the template (or the version specified by "-v").
    No updating will happen when using this option.
    """
    if check:
        if footing.update.up_to_date(version=version):
            print('Footing package is up to date')
        else:
            msg = (
                'This footing package is out of date with the latest template.'
                ' Update your package by running "footing update" and commiting changes.'
            )
            raise footing.exceptions.NotUpToDateWithTemplateError(msg)
    else:
        footing.update.update(new_version=version, enter_parameters=enter_parameters)


@main.command()
@click.argument('forge', nargs=1, required=True)
@click.argument('template', nargs=1, required=False)
@click.option(
    '-l',
    '--long-format',
    is_flag=True,
    help='Print extended information about results',
)
def ls(forge, template, long_format):
    """
    List packages created with footing. Enter a git forge path, such as a Github
    user or Gitlab group URL, to list all templates under the forge.
    Provide the template path as the second argument to list all projects
    that have been started with that template.

    Use "-l" to print the repository descriptions of templates
    or projects.
    """
    results = footing.ls.ls(forge, template=template)
    for ssh_path, description in results.items():
        if long_format:
            print(ssh_path, '-', description)
        else:
            print(ssh_path)


@main.command()
def clean():
    """
    Cleans temporary resources created by footing, such as the footing update branch
    """
    footing.clean.clean()


@main.command()
@click.argument('template', nargs=1, required=True)
@click.option(
    '-v',
    '--version',
    default=None,
    help='Git SHA or branch of template to use for update',
)
def switch(template, version):
    """
    Switch a project's template to a different template.
    """
    footing.update.update(new_template=template, new_version=version)
