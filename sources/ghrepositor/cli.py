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


''' Command-line interface. '''


from . import __

from . import github as _github

from .exceptions import Omnierror


class EnvironmentConfigurationError( Omnierror, RuntimeError ):
    ''' Environment configuration error. '''


def execute( ) -> None:
    ''' Entrypoint for CLI execution. '''
    from asyncio import run
    config = (
        __.tyro.conf.EnumChoicesFromValues,
        __.tyro.conf.HelptextFromCommentsOff,
    )
    try: run( __.tyro.cli( _main, config = config )( ) ) # pyright: ignore
    except SystemExit: raise
    except BaseException:
        # TODO: Log exception.
        raise SystemExit( 1 ) from None


def _get_environment_variables( ) -> tuple[ str, str, str ]:
    ''' Retrieves required environment variables. '''
    try:
        github_token = __.os.environ[ 'GITHUB_TOKEN' ]
    except KeyError as exception:
        raise EnvironmentConfigurationError(  # noqa: TRY003
            "GITHUB_TOKEN environment variable not set."
        ) from exception
    try:
        gpg_signing_key = __.os.environ[ 'GPG_SIGNING_KEY' ]
    except KeyError as exception:
        raise EnvironmentConfigurationError(  # noqa: TRY003
            "GPG_SIGNING_KEY environment variable not set."
        ) from exception
    try:
        anthropic_api_key = __.os.environ[ 'ANTHROPIC_API_KEY' ]
    except KeyError as exception:
        raise EnvironmentConfigurationError(  # noqa: TRY003
            "ANTHROPIC_API_KEY environment variable not set."
        ) from exception
    return github_token, gpg_signing_key, anthropic_api_key


async def _configure_repository_secrets(
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
    gpg_signing_key: str,
    anthropic_api_key: str,
) -> None:
    ''' Configures repository secrets. '''
    print( "Retrieving repository public key..." )
    public_key_info = await _github.get_repository_public_key(
        client, repository_owner, repository_name )
    print( "Adding repository secrets..." )
    secrets = __.immut.Dictionary( {
        'GHA_COMMIT_SIGNING_KEY': gpg_signing_key,
        'ANTHROPIC_API_KEY': anthropic_api_key,
    } )
    for secret_name, secret_value in secrets.items( ):
        await _github.add_repository_secret(
            client,
            repository_owner,
            repository_name,
            secret_name,
            secret_value,
            public_key_info )


async def _configure_branch_protections(
    client: __.httpx.AsyncClient,
    repository_id: str,
) -> None:
    ''' Configures branch protection rules. '''
    print( "Configuring branch protection rules..." )
    branch_patterns = ( 'master', 'release-*' )
    for pattern in branch_patterns:
        await _github.configure_branch_protection(
            client, repository_id, pattern )


async def _configure_pages_and_deployments(
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
) -> None:
    ''' Configures GitHub Pages and deployment policies. '''
    print( "Configuring GitHub Pages..." )
    await _github.configure_github_pages(
        client, repository_owner, repository_name )
    print( "Configuring deployment branch policies..." )
    deployment_policies = (
        { 'name': 'master', 'type': 'branch' },
        { 'name': 'v[0-9]*', 'type': 'tag' },
    )
    await _github.configure_deployment_policies(
        client, repository_owner, repository_name, deployment_policies )


async def _main( repository_name: str ) -> None:
    ''' Creates and configures GitHub repository.

    Args:
        repository_name: Name for new repository
    '''
    try:
        github_token, gpg_signing_key, anthropic_api_key = (
            _get_environment_variables( ) )
    except EnvironmentConfigurationError as exception:
        raise SystemExit( f"ERROR: {exception}" ) from exception  # noqa: TRY003

    headers = {
        'Authorization': f"token {github_token}",
        'Accept': 'application/vnd.github+json',
    }

    async with __.httpx.AsyncClient( headers = headers ) as client:
        print( f"Creating repository: {repository_name}" )
        repository_info = await _github.create_repository(
            client, repository_name, is_private = False )
        try:
            repository_owner = repository_info[ 'owner' ][ 'login' ]
            repository_id = repository_info[ 'node_id' ]
        except KeyError as exception:
            message = "Repository response missing expected fields."
            raise _github.RepositoryCreationError( message ) from exception
        await _configure_repository_secrets(
            client,
            repository_owner,
            repository_name,
            gpg_signing_key,
            anthropic_api_key )
        await _configure_branch_protections(
            client, repository_id )
        await _configure_pages_and_deployments(
            client, repository_owner, repository_name )
        print( f"\nSuccessfully configured repository: {repository_name}" )
        print(
            f"Repository URL: https://github.com/{repository_owner}/"
            f"{repository_name}" )
