import collections

import pytest

import footing.forge
import footing.ls


@pytest.mark.parametrize(
    'forge, template, github_query',
    [
        ('github.com/u', None, 'user:u filename:cookiecutter.json'),
        ('github.com/u/', None, 'user:u filename:cookiecutter.json'),
        (
            'github.com/u',
            'git@github.com:u/t.git',
            'user:u filename:footing.yaml t',
        ),
    ],
)
def test_ls(forge, template, github_query, mocker):
    mock_code_search = mocker.patch.object(
        footing.forge.Github,
        '_code_search',
        autospec=True,
        return_value={
            'repo2': {'description': 'description 2'},
            'repo1': {'description': 'description 1'},
        },
    )

    results = footing.ls.ls(forge, template=template)

    mock_code_search.assert_called_once_with(mocker.ANY, github_query, forge=forge)
    assert results == collections.OrderedDict(
        [
            ('repo1', 'description 1'),
            ('repo2', 'description 2'),
        ]
    )
