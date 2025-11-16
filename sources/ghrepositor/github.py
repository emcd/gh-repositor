# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' GitHub API client for repository management. '''


from . import __

from . import exceptions as _exceptions


RepositoryData: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
SecretsPublicKey: __.typx.TypeAlias = __.cabc.Mapping[ str, str ]


def encrypt_secret( public_key: str, secret_value: str ) -> str:
    ''' Encrypts secret value using repository public key. '''
    try:
        decoded_key = __.nacl.public.PublicKey(
            public_key.encode( 'utf-8' ),
            __.nacl.encoding.Base64Encoder( ) )
    except Exception as exception:
        raise _exceptions.PublicKeyDecodingFailure(
            public_key[ :20 ]
        ) from exception
    sealed_box = __.nacl.public.SealedBox( decoded_key )
    try:
        encrypted: bytes = sealed_box.encrypt( secret_value.encode( 'utf-8' ) )
    except Exception as exception:
        raise _exceptions.SecretValueEncryptionFailure( ) from exception
    return __.base64.b64encode( encrypted ).decode( 'utf-8' )


async def create_repository(
    client: __.httpx.AsyncClient,
    repository_name: str,
    *,
    is_private: bool = False,
) -> RepositoryData:
    ''' Creates GitHub repository via API. '''
    url = 'https://api.github.com/user/repos'
    data: dict[ str, __.typx.Any ] = {
        'name': repository_name, 'private': is_private }
    try:
        response = await client.post( url, json = data )
        response.raise_for_status( )
    except __.httpx.HTTPStatusError as exception:
        raise _exceptions.RepositoryCreationFailure(
            repository_name,
            status_code = exception.response.status_code,
            response_text = exception.response.text
        ) from exception
    except Exception as exception:
        raise _exceptions.RepositoryCreationFailure(
            repository_name
        ) from exception
    return __.immut.Dictionary( response.json( ) )


async def get_repository_public_key(
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
) -> SecretsPublicKey:
    ''' Retrieves repository public key for secrets encryption. '''
    url = (
        f"https://api.github.com/repos/{repository_owner}/"
        f"{repository_name}/actions/secrets/public-key" )
    try:
        response = await client.get( url )
        response.raise_for_status( )
    except __.httpx.HTTPStatusError as exception:
        raise _exceptions.PublicKeyRetrievalFailure(
            repository_owner,
            repository_name,
            status_code = exception.response.status_code
        ) from exception
    except Exception as exception:
        raise _exceptions.PublicKeyRetrievalFailure(
            repository_owner,
            repository_name
        ) from exception
    return __.immut.Dictionary( response.json( ) )


async def add_repository_secret(  # noqa: PLR0913
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
    secret_name: str,
    secret_value: str,
    public_key_info: SecretsPublicKey,
) -> None:
    ''' Adds encrypted secret to repository. '''
    try:
        encrypted_value = encrypt_secret(
            public_key_info[ 'key' ], secret_value )
    except KeyError as exception:
        raise _exceptions.PublicKeyInformationAbsence(
            'key'
        ) from exception
    try:
        key_id = public_key_info[ 'key_id' ]
    except KeyError as exception:
        raise _exceptions.PublicKeyInformationAbsence(
            'key_id'
        ) from exception
    url = (
        f"https://api.github.com/repos/{repository_owner}/"
        f"{repository_name}/actions/secrets/{secret_name}" )
    data = { 'encrypted_value': encrypted_value, 'key_id': key_id }
    try:
        response = await client.put( url, json = data )
        response.raise_for_status( )
    except __.httpx.HTTPStatusError as exception:
        raise _exceptions.SecretAdditionFailure(
            secret_name,
            status_code = exception.response.status_code
        ) from exception
    except Exception as exception:
        raise _exceptions.SecretAdditionFailure(
            secret_name
        ) from exception


async def configure_branch_protection(
    client: __.httpx.AsyncClient,
    repository_id: str,
    branch_pattern: str,
) -> None:
    ''' Configures branch protection rule via GraphQL API. '''
    query = f'''
mutation {{
  createBranchProtectionRule(input: {{
    repositoryId: "{repository_id}",
    pattern: "{branch_pattern}",
    requiresCommitSignatures: true
  }}) {{
    clientMutationId
  }}
}}
'''
    url = 'https://api.github.com/graphql'
    data = { 'query': query }
    try:
        response = await client.post( url, json = data )
        response.raise_for_status( )
    except __.httpx.HTTPStatusError as exception:
        raise _exceptions.BranchProtectionFailure(
            branch_pattern,
            status_code = exception.response.status_code
        ) from exception
    except Exception as exception:
        raise _exceptions.BranchProtectionFailure(
            branch_pattern
        ) from exception


async def _create_pages_environment(
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
) -> None:
    ''' Creates GitHub Pages environment for repository. '''
    env_url = (
        f"https://api.github.com/repos/{repository_owner}/"
        f"{repository_name}/environments/github-pages" )
    env_data: dict[ str, __.typx.Any ] = {
        'wait_timer': 0,
        'reviewers': [ ],
        'deployment_branch_policy': {
            'protected_branches': False,
            'custom_branch_policies': True,
        }
    }
    try:
        response = await client.put( env_url, json = env_data )
        response.raise_for_status( )
    except __.httpx.HTTPStatusError as exception:
        raise _exceptions.PagesEnvironmentCreationFailure(
            status_code = exception.response.status_code
        ) from exception
    except Exception as exception:
        raise _exceptions.PagesEnvironmentCreationFailure( ) from exception


async def _configure_pages_build_type(
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
) -> None:
    ''' Configures GitHub Pages build type for repository. '''
    pages_url = (
        f"https://api.github.com/repos/{repository_owner}/"
        f"{repository_name}/pages" )
    pages_data: dict[ str, __.typx.Any ] = {
        'source': {
            'branch': 'master',
            'path': '/',
        },
        'build_type': 'workflow'
    }
    try:
        response = await client.post( pages_url, json = pages_data )
        response.raise_for_status( )
    except __.httpx.HTTPStatusError as exception:
        raise _exceptions.PagesBuildConfigurationFailure(
            status_code = exception.response.status_code
        ) from exception
    except Exception as exception:
        raise _exceptions.PagesBuildConfigurationFailure( ) from exception


async def configure_github_pages(
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
) -> None:
    ''' Configures GitHub Pages for repository. '''
    await _create_pages_environment(
        client, repository_owner, repository_name )
    await _configure_pages_build_type(
        client, repository_owner, repository_name )


async def configure_deployment_policies(
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
    policies: __.cabc.Sequence[
        __.cabc.Mapping[ str, str ]
    ],
) -> None:
    ''' Configures deployment branch policies for GitHub Pages. '''
    url = (
        f"https://api.github.com/repos/{repository_owner}/"
        f"{repository_name}/environments/github-pages/"
        "deployment-branch-policies" )
    for policy in policies:
        try:
            response = await client.post( url, json = policy )
            response.raise_for_status( )
        except __.httpx.HTTPStatusError as exception:  # noqa: PERF203
            raise _exceptions.DeploymentPolicyConfigurationFailure(
                policy,
                status_code = exception.response.status_code
            ) from exception
        except Exception as exception:
            raise _exceptions.DeploymentPolicyConfigurationFailure(
                policy
            ) from exception
