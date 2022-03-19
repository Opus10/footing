"""Tests for footing.cli module"""
# pylint: disable=no-value-for-parameter
import collections
import sys

import click
import pkg_resources
import pytest

import footing.cli
import footing.exceptions


@pytest.fixture
def mock_exit(mocker):
    yield mocker.patch('sys.exit', autospec=True)


@pytest.fixture
def mock_successful_exit(mock_exit):
    yield
    mock_exit.assert_called_once_with(0)


@pytest.mark.usefixtures('mock_successful_exit')
@pytest.mark.parametrize(
    'subcommand, args, expected_function, exp_call_args, exp_call_kwargs',
    [
        ('setup', ['t'], 'footing.setup.setup', ['t'], {'version': None}),
        (
            'setup',
            ['t', '-v', 'v1'],
            'footing.setup.setup',
            ['t'],
            {'version': 'v1'},
        ),
        (
            'update',
            [],
            'footing.update.update',
            [],
            {'new_version': None, 'enter_parameters': False},
        ),
        (
            'update',
            ['-c', '-v', 'v1'],
            'footing.update.up_to_date',
            [],
            {'version': 'v1'},
        ),
        ('ls', ['user'], 'footing.ls.ls', ['user'], {'template': None}),
        (
            'ls',
            ['user', 'template'],
            'footing.ls.ls',
            ['user'],
            {'template': 'template'},
        ),
        ('clean', [], 'footing.clean.clean', [], {}),
        (
            'switch',
            ['new_t', '-v', 'new_v'],
            'footing.update.update',
            [],
            {'new_template': 'new_t', 'new_version': 'new_v'},
        ),
    ],
)
def test_main(subcommand, args, expected_function, exp_call_args, exp_call_kwargs, mocker):
    """Verify calling the CLI subcommands works as expected"""
    mocker.patch.object(sys, 'argv', ['footing', subcommand] + args)
    mock_expected_func = mocker.patch(expected_function, autospec=True)

    footing.cli.main()

    mock_expected_func.assert_called_once_with(*exp_call_args, **exp_call_kwargs)


@pytest.mark.usefixtures('mock_successful_exit')
def test_main_w_version(mocker, capsys):
    """Test calling the CLI with the --version option"""
    mocker.patch.object(sys, 'argv', ['footing', '--version'])

    footing.cli.main()

    out, _ = capsys.readouterr()
    version = pkg_resources.get_distribution('footing').version
    assert out == 'footing %s\n' % version


@pytest.mark.usefixtures('mock_successful_exit')
def test_main_no_args(mocker, capsys):
    """Test calling the CLI with no options"""
    mocker.patch.object(sys, 'argv', ['footing'])
    mocker.patch.object(click.Context, 'get_help', autospec=True, return_value='help_text')

    footing.cli.main()

    out, _ = capsys.readouterr()
    assert out == 'help_text\n'


@pytest.mark.usefixtures('mock_exit')
@pytest.mark.parametrize(
    'version, up_to_date_return',
    [
        pytest.param(
            None,
            False,
            marks=pytest.mark.xfail(raises=footing.exceptions.NotUpToDateWithTemplateError),
        ),
        (None, True),
        ('version', True),
    ],
)
def test_update_check(version, up_to_date_return, capsys, mocker):
    """Verifies checking for updates when calling footing update -c"""
    mocker.patch.object(sys, 'argv', ['footing', 'update', '-c', '-v', version])
    mock_up_to_date = mocker.patch(
        'footing.update.up_to_date',
        autospec=True,
        return_value=up_to_date_return,
    )

    footing.cli.main()

    out, _ = capsys.readouterr()
    assert out == 'Footing package is up to date\n'
    mock_up_to_date.assert_called_once_with(version=version)


@pytest.mark.usefixtures('mock_successful_exit')
@pytest.mark.parametrize(
    'ls_args, expected_out',
    [
        (['footing', 'ls', 'user'], 'ls\nvalues\n'),
        (
            ['footing', 'ls', 'user', '-l'],
            'ls - ls descr\nvalues - (no project description found)\n',
        ),
    ],
)
def test_ls(ls_args, expected_out, capsys, mocker):
    """Verify ls prints results properly"""
    mocker.patch(
        'footing.ls.ls',
        autospec=True,
        return_value=collections.OrderedDict(
            [
                ('ls', 'ls descr'),
                ('values', '(no project description found)'),
            ]
        ),
    )
    mocker.patch.object(sys, 'argv', ls_args)

    footing.cli.main()

    out, _ = capsys.readouterr()
    assert out == expected_out
