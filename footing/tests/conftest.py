"""Footing test setup and fixtures"""
import os

import pytest
import responses as responses_lib

import footing.constants


@pytest.fixture
def github_env(mocker):
    """Sets Github environment variables"""
    gh_env = {footing.constants.GITHUB_API_TOKEN_ENV_VAR: 'test_gh_token'}
    mocker.patch.dict(os.environ, gh_env)
    return gh_env


@pytest.fixture(autouse=True)
def footing_env(github_env):
    """Provides a complete test footing environment for testing"""
    return github_env


@pytest.fixture
def responses():
    """Ensure no http requests happen and allow for mocking out responses"""
    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as mocked_requests:
        yield mocked_requests
