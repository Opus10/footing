"""
footing.constants
~~~~~~~~~~~~~~~~~

Constants for footing
"""

#: The environment variable set when running any footing command. It is set to
#: the name of the command
FOOTING_ENV_VAR = '_FOOTING'

#: The footing config file in each repo
FOOTING_CONFIG_FILE = 'footing.yaml'

#: The Github API token environment variable
GITHUB_API_TOKEN_ENV_VAR = 'GITHUB_API_TOKEN'

#: The Gitlab API token environment variable
GITLAB_API_TOKEN_ENV_VAR = 'GITLAB_API_TOKEN'

#: Footing docs URL
FOOTING_DOCS_URL = 'https://github.com/Opus10/footing'

#: The temporary branches used for updates
UPDATE_BRANCH_NAME = '_footing_update'
TEMP_UPDATE_BRANCH_NAME = UPDATE_BRANCH_NAME + '_temp'
