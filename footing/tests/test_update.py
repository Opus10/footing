"""Tests for footing.update module"""
import subprocess

import pytest

import footing.constants
import footing.forge
import footing.update


def test_get_latest_template_version(mocker):
    """Tests footing.update._get_latest_template_version"""
    mocker.patch.object(
        footing.forge.Github,
        'get_latest_template_version',
        autospec=True,
        return_value='v1',
    )
    assert footing.update._get_latest_template_version('git@github.com:org/template.git') == 'v1'


@pytest.mark.parametrize(
    'old_config, new_config, expected_has_changed',
    [
        ('{"config": "same"}', '{"config": "same"}', False),
        ('{"config": "same"}', '{"config": "diff"}', True),
    ],
)
def test_cookiecutter_configs_have_changed(
    old_config, new_config, expected_has_changed, mocker, responses
):
    """Tests footing.update._cookiecutter_configs_have_changed"""
    mock_clone = mocker.patch('footing.update.cc_vcs.clone', autospec=True, return_value='path')
    mock_open = mocker.patch('footing.update.open')
    mock_open().read.side_effect = [old_config, new_config]
    mock_call = mocker.patch('subprocess.check_call', autospec=True)
    template = 'git@github.com:org/template.git'

    config_has_changed = footing.update._cookiecutter_configs_have_changed(template, 'old', 'new')
    assert config_has_changed == expected_has_changed
    mock_clone.assert_called_once_with(template, 'old', mocker.ANY)
    assert mock_call.call_count == 1


@pytest.mark.parametrize('existing_files', [True, False])
def test_apply_template(mocker, existing_files):
    mock_td = mocker.patch('tempfile.TemporaryDirectory', autospec=True)
    mock_cc = mocker.patch(
        'cookiecutter.main.cookiecutter',
        autospec=True,
        return_value='basepath',
    )
    mock_list = mocker.patch('os.listdir', autospec=True, return_value=['a', 'b'])
    mocker.patch('os.path.isdir', autospec=True, side_effect=[True, False])
    mocker.patch('os.path.exists', autospec=True, return_value=existing_files)
    mock_shutil_ct = mocker.patch('shutil.copytree', autospec=True)
    mock_shutil_cp = mocker.patch('shutil.copy2', autospec=True)
    mock_rmtree = mocker.patch('shutil.rmtree', autospec=True)
    mock_remove = mocker.patch('os.remove', autospec=True)

    footing.update._apply_template('t', '.', checkout='v1', extra_context={'c': 'tx'})

    mock_cc.assert_called_once_with(
        't',
        checkout='v1',
        no_input=True,
        output_dir=mock_td.return_value.__enter__.return_value,
        extra_context={'c': 'tx'},
    )
    mock_list.assert_called_once_with(mock_cc.return_value)
    mock_shutil_ct.assert_called_once_with('basepath/a', './a')
    mock_shutil_cp.assert_called_once_with('basepath/b', './b')
    if existing_files:
        mock_rmtree.assert_called_once_with('./a')
        mock_remove.assert_called_once_with('./b')
    else:
        assert not mock_rmtree.called
        assert not mock_remove.called


@pytest.mark.parametrize(
    'footing_config, latest_version, supplied_version, expected_up_to_date',
    [
        ({'_version': 'v1', '_template': 't'}, 'v2', None, False),
        ({'_version': 'v1', '_template': 't'}, 'v1', None, True),
        ({'_version': 'v1', '_template': 't'}, 'v1', 'v2', False),
        ({'_version': 'v3', '_template': 't'}, 'v1', 'v3', True),
    ],
)
def test_up_to_date(
    footing_config,
    latest_version,
    supplied_version,
    expected_up_to_date,
    mocker,
):
    """Tests footing.update.up_to_date"""
    mocker.patch('footing.check.in_git_repo', autospec=True)
    mocker.patch('footing.check.in_clean_repo', autospec=True)
    mocker.patch('footing.check.is_footing_project', autospec=True)
    mocker.patch(
        'footing.utils.read_footing_config',
        autospec=True,
        return_value=footing_config,
    )
    mocker.patch(
        'footing.update._get_latest_template_version',
        autospec=True,
        return_value=latest_version,
    )

    assert footing.update.up_to_date(version=supplied_version) == expected_up_to_date


@pytest.mark.parametrize(
    'version, supplied_version, latest_version',
    [
        ('v1', None, 'v1'),
        ('v1', 'v1', 'v0'),
    ],
)
def test_update_w_up_to_date(version, supplied_version, latest_version, mocker):
    """Tests footing.update.update when the template is already up to date"""
    mocker.patch('footing.check.not_has_branch', autospec=True)
    mocker.patch('footing.check.in_git_repo', autospec=True)
    mocker.patch('footing.check.in_clean_repo', autospec=True)
    mocker.patch('footing.check.is_footing_project', autospec=True)
    mocker.patch(
        'footing.utils.read_footing_config',
        autospec=True,
        return_value={'_version': version, '_template': 't'},
    )
    mocker.patch(
        'footing.update._get_latest_template_version',
        autospec=True,
        return_value=latest_version,
    )

    assert not footing.update.update(new_version=supplied_version)


@pytest.mark.parametrize(
    'cc_configs_changed, enter_parameters, current_version, latest_version, old_template',
    [
        (False, False, 'v1', 'v2', None),
        (False, False, 'v1', 'v2', 'git@github.com:owner/old_repo.git'),
        (True, False, 'v1', 'v2', None),
        (False, True, 'v1', 'v2', None),
        # Updates should still proceed when entering parameters and up to date with latest
        (False, True, 'v1', 'v1', None),
    ],
)
def test_update_w_out_of_date(
    cc_configs_changed,
    enter_parameters,
    current_version,
    latest_version,
    old_template,
    mocker,
    fs,
):
    """Tests footing.update.update when the template is out of date"""
    template = 'git@github.com:owner/repo.git'
    footing_config = {'_version': current_version, '_template': template}
    mocker.patch('footing.check.in_git_repo', autospec=True)
    mocker.patch('footing.check.in_clean_repo', autospec=True)
    mocker.patch('footing.check.is_footing_project', autospec=True)
    mocker.patch('footing.check.not_has_branch', autospec=True)
    mocker.patch(
        'footing.utils.read_footing_config',
        autospec=True,
        return_value=footing_config,
    )
    mocker.patch(
        'footing.update._get_latest_template_version',
        autospec=True,
        return_value=latest_version,
    )
    mock_apply_template = mocker.patch('footing.update._apply_template', autospec=True)
    mock_cc_configs_have_changed = mocker.patch(
        'footing.update._cookiecutter_configs_have_changed',
        autospec=True,
        return_value=cc_configs_changed,
    )
    mock_input = mocker.patch('builtins.input', autospec=True)
    mock_get_cc_config = mocker.patch(
        'footing.utils.get_cookiecutter_config',
        autospec=True,
        return_value=('repo', footing_config),
    )
    mock_shell = mocker.patch('footing.utils.shell', autospec=True)
    mock_write_config = mocker.patch('footing.utils.write_footing_config', autospec=True)

    footing.update.update(enter_parameters=enter_parameters, old_template=old_template)

    assert mock_input.called == cc_configs_changed or old_template is not None
    assert mock_get_cc_config.called == (
        cc_configs_changed or enter_parameters or old_template is not None
    )
    assert mock_apply_template.call_args_list == [
        mocker.call(
            old_template or template,
            '.',
            checkout=current_version,
            extra_context=footing_config,
        ),
        mocker.call(
            template,
            '.',
            checkout=latest_version,
            extra_context=footing_config,
        ),
    ]
    mock_write_config.assert_called_once_with(footing_config, template, latest_version)
    if not old_template:
        mock_cc_configs_have_changed.assert_called_once_with(
            template, current_version, latest_version
        )
    else:
        assert not mock_cc_configs_have_changed.called

    assert mock_shell.call_args_list == [
        mocker.call('git checkout -b _footing_update', stderr=subprocess.DEVNULL),
        mocker.call(
            'git checkout --orphan _footing_update_temp',
            stderr=subprocess.DEVNULL,
        ),
        mocker.call('git rm -rf .', stdout=subprocess.DEVNULL),
        mocker.call('git add .'),
        mocker.call(
            'git commit --no-verify -m "Initialize template from version {}"'.format(
                current_version
            ),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        mocker.call('git checkout _footing_update', stderr=subprocess.DEVNULL),
        mocker.call(
            'git merge -s ours --no-edit --allow-unrelated-histories ' '_footing_update_temp',
            stderr=subprocess.DEVNULL,
        ),
        mocker.call('git checkout _footing_update_temp', stderr=subprocess.DEVNULL),
        mocker.call('git rm -rf .', stdout=subprocess.DEVNULL),
        mocker.call('git add .'),
        mocker.call(
            'git commit --no-verify -m "Update template to version {}"'.format(latest_version),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        mocker.call('git checkout _footing_update', stderr=subprocess.DEVNULL),
        mocker.call(
            'git merge --no-commit _footing_update_temp',
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        mocker.call(
            'git checkout --theirs footing.yaml',
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        mocker.call('git branch -D _footing_update_temp', stdout=subprocess.DEVNULL),
    ]
