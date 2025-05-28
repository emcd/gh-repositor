import os
import sys

from base64 import b64encode

import requests

from dotenv import load_dotenv
from nacl import encoding, public


load_dotenv( )


GITHUB_TOKEN = os.environ[ 'GITHUB_TOKEN' ]
GPG_SIGNING_KEY = os.environ[ 'GPG_SIGNING_KEY' ]
GH_PROJECT_NAME = os.environ[ 'GH_PROJECT_NAME' ]

# Get Anthropic API key from environment
ANTHROPIC_API_KEY = os.environ.get( 'ANTHROPIC_API_KEY' )
if not ANTHROPIC_API_KEY:
    print(
        "ERROR: ANTHROPIC_API_KEY not found in environment or .env file",
        file = sys.stderr )
    sys.exit( 1 )


headers = {
    'Authorization': f"token {GITHUB_TOKEN}",
    'Accept': 'application/vnd.github+json',
}


def encrypt( public_key: str, secret_value: str ) -> str:
    ''' Encrypt a Unicode string using the public key. '''
    public_key = public.PublicKey(
        public_key.encode( "utf-8" ), encoding.Base64Encoder( ) )
    sealed_box = public.SealedBox( public_key )
    encrypted = sealed_box.encrypt( secret_value.encode( "utf-8" ) )
    return b64encode( encrypted ).decode( "utf-8" )


def add_repository_secret(
    repo_owner: str,
    repo_name: str,
    secret_name: str,
    secret_value: str,
    public_key_info: dict,
) -> None:
    ''' Add an encrypted secret to the repository. '''
    encrypted_value = encrypt( public_key_info[ 'key' ], secret_value )
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/{secret_name}"
    data = { 'encrypted_value': encrypted_value, 'key_id': public_key_info[ 'key_id' ] }
    response = requests.put( url, json = data, headers = headers )
    response.raise_for_status( )


# Create an empty repository
url = 'https://api.github.com/user/repos'
data = { 'name': GH_PROJECT_NAME, 'private': False }
response = requests.post( url, json = data, headers = headers )
response.raise_for_status( )
repo_info = response.json( )
repo_owner = repo_info[ 'owner' ][ 'login' ]

# Get the public key for the repository
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/actions/secrets/public-key"
response = requests.get( url, headers = headers )
response.raise_for_status( )
public_key_info = response.json( )

add_repository_secret(
    repo_owner,
    GH_PROJECT_NAME,
    'GHA_COMMIT_SIGNING_KEY',
    GPG_SIGNING_KEY,
    public_key_info )
add_repository_secret(
    repo_owner,
    GH_PROJECT_NAME,
    'ANTHROPIC_API_KEY',
    ANTHROPIC_API_KEY,
    public_key_info )

# GraphQL query to set protection rules for master and release-* branches
query = f'''
mutation {{
  masterRule: createBranchProtectionRule(input: {{
    repositoryId: "{repo_info['node_id']}",
    pattern: "master",
    requiresCommitSignatures: true
  }}) {{
    clientMutationId
  }}
  releaseRule: createBranchProtectionRule(input: {{
    repositoryId: "{repo_info['node_id']}",
    pattern: "release-*",
    requiresCommitSignatures: true
  }}) {{
    clientMutationId
  }}
}}
'''

url = 'https://api.github.com/graphql'
data = { 'query': query }
response = requests.post( url, json = data, headers = headers )
response.raise_for_status( )

# Create GitHub Pages environment
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/environments/github-pages"
data = {
    'wait_timer': 0,
    'reviewers': [ ],
    'deployment_branch_policy': {
        'protected_branches': False,
        'custom_branch_policies': True,
    }
}
response = requests.put( url, json = data, headers = headers )
response.raise_for_status( )

# Configure GitHub Pages to use GitHub Actions as source
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/pages"
data = {
    'source': {
        'branch': 'master',  # Required but not actually used
        'path': '/',         # Required but not actually used
    },
    'build_type': 'workflow'
}
response = requests.post( url, json = data, headers = headers )
response.raise_for_status( )

# Set the deployment branch policy for the master branch and release tags
# https://docs.github.com/en/rest/deployments/branch-policies?apiVersion=2022-11-28#create-a-deployment-branch-policy
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/environments/github-pages/deployment-branch-policies"
for data in (
    { 'name': 'master', 'type': 'branch' },
    { 'name': 'v[0-9]*', 'type': 'tag' },
):
    response = requests.post( url, json = data, headers = headers )
    response.raise_for_status( )

print( "Successfully configured the repository." )
