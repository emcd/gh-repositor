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

from . import exceptions as _exceptions
from . import github as _github


_scribe = __.acquire_scribe( __name__ )


def intercept_errors( ) -> __.cabc.Callable[
    [ __.cabc.Callable[
        ..., __.typx.Coroutine[ __.typx.Any, __.typx.Any, None ] ] ],
    __.cabc.Callable[
        ..., __.typx.Coroutine[ __.typx.Any, __.typx.Any, None ] ]
]:
    ''' Decorator for CLI handlers to intercept exceptions.

        Catches Omnierror exceptions and renders them appropriately.
        Other exceptions are logged and formatted simply.
    '''
    def decorator(
        function: __.cabc.Callable[
            ..., __.typx.Coroutine[ __.typx.Any, __.typx.Any, None ] ]
    ) -> __.cabc.Callable[
        ..., __.typx.Coroutine[ __.typx.Any, __.typx.Any, None ]
    ]:
        @__.funct.wraps( function )
        async def wrapper(
            self: __.typx.Any,
            auxdata: __.Globals,
            *posargs: __.typx.Any,
            **nomargs: __.typx.Any,
        ) -> None:
            try: return await function( self, auxdata, *posargs, **nomargs )
            except _exceptions.Omnierror as exc:
                error_message = __.json.dumps( {
                    "type": type( exc ).__name__,
                    "message": str( exc ),
                }, indent = 2 )
                print( error_message )
                raise SystemExit( 1 ) from None
            except Exception as exc:
                _scribe.error( f"{function.__name__} failed: %s", exc )
                error_message = __.json.dumps( {
                    "type": "unexpected_error",
                    "message": str( exc ),
                }, indent = 2 )
                print( error_message )
                raise SystemExit( 1 ) from None

        return wrapper
    return decorator


def _retrieve_github_token( ) -> __.Absential[ str ]:
    ''' Retrieves GitHub token from environment or gh CLI. '''
    # Try environment variable first
    token = __.os.environ.get( 'GITHUB_TOKEN' )
    if token: return token
    # Fallback to gh auth token
    try:
        result = __.subprocess.run(
            [ 'gh', 'auth', 'token' ],
            capture_output = True,
            text = True,
            check = True,
            timeout = 5 )
        token = result.stdout.strip( )
        if token: return token
    except ( FileNotFoundError, __.subprocess.CalledProcessError, __.subprocess.TimeoutExpired ):  # noqa: E501
        pass
    return __.absent


def _retrieve_gpg_signing_key( ) -> __.Absential[ str ]:
    ''' Retrieves GPG signing key from environment or GPG keyring. '''
    # Try environment variable first
    key = __.os.environ.get( 'GPG_SIGNING_KEY' )
    if key: return key
    # Fallback to parsing GPG keyring for GitHub Actions Robot key
    try:
        # List secret keys with fingerprints
        list_result = __.subprocess.run(
            [ 'gpg', '--list-secret-keys', '--with-subkey-fingerprints' ],
            capture_output = True,
            text = True,
            check = True,
            timeout = 5 )
        # Find key ID for GitHub Actions Robot
        lines = list_result.stdout.split( '\n' )
        key_id = None
        found_github_actions = False
        for line in lines:
            if 'Github Actions Robot' in line:
                found_github_actions = True
            elif found_github_actions and line.strip( ):
                # Get the fingerprint from the line after uid
                parts = line.strip( ).split( )
                if parts:
                    key_id = parts[ 0 ]
                    break
        if not key_id: return __.absent
        # Export the key
        export_result = __.subprocess.run(
            [ 'gpg', '--armor', '--export-secret-subkeys', key_id ],
            capture_output = True,
            text = True,
            check = True,
            timeout = 5 )
        exported_key = export_result.stdout.strip( )
        if exported_key: return exported_key
    except ( FileNotFoundError, __.subprocess.CalledProcessError, __.subprocess.TimeoutExpired ):  # noqa: E501
        pass
    return __.absent


def _retrieve_anthropic_api_key( ) -> __.Absential[ str ]:
    ''' Retrieves Anthropic API key from environment or .env file. '''
    # Try environment variable first
    key = __.os.environ.get( 'ANTHROPIC_API_KEY' )
    if key: return key
    # Fallback to .env file
    env_path = __.pathlib.Path( '.env' )
    if env_path.exists( ):
        try:
            with env_path.open( ) as f:
                for raw_line in f:
                    line = raw_line.strip( )
                    if line.startswith( 'ANTHROPIC_API_KEY=' ):
                        key = line.split( '=', 1 )[ 1 ].strip( )
                        # Remove quotes if present
                        if key.startswith( ( '"', "'" ) ) and key[ 0 ] == key[ -1 ]:  # noqa: E501
                            key = key[ 1:-1 ]
                        if key: return key
        except ( OSError, UnicodeDecodeError ):
            pass
    return __.absent


def _retrieve_credentials( ) -> tuple[ str, str, str ]:
    ''' Retrieves required credentials with fallback logic. '''
    github_token = _retrieve_github_token( )
    if __.is_absent( github_token ):
        raise _exceptions.EnvironmentConfigurationAbsence( 'GITHUB_TOKEN' )
    gpg_signing_key = _retrieve_gpg_signing_key( )
    if __.is_absent( gpg_signing_key ):
        raise _exceptions.EnvironmentConfigurationAbsence( 'GPG_SIGNING_KEY' )
    anthropic_api_key = _retrieve_anthropic_api_key( )
    if __.is_absent( anthropic_api_key ):
        raise _exceptions.EnvironmentConfigurationAbsence( 'ANTHROPIC_API_KEY' )  # noqa: E501
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


class Cli( __.appcore_cli.Application, decorators = ( __.standard_tyro_class, ) ):  # noqa: E501
    ''' GitHub repository creation and configuration CLI. '''

    repository_name: __.typx.Annotated[
        __.tyro.conf.Positional[ str ],
        __.tyro.conf.arg( help = "Name for new repository" ),
    ]

    @intercept_errors( )
    async def execute( self, auxdata: __.Globals ) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        ''' Creates and configures GitHub repository. '''
        github_token, gpg_signing_key, anthropic_api_key = (
            _retrieve_credentials( ) )

        headers = {
            'Authorization': f"token {github_token}",
            'Accept': 'application/vnd.github+json',
        }

        async with __.httpx.AsyncClient( headers = headers ) as client:
            print( f"Creating repository: {self.repository_name}" )
            repository_info = await _github.create_repository(
                client, self.repository_name, is_private = False )
            try:
                repository_owner = repository_info[ 'owner' ][ 'login' ]
                repository_id = repository_info[ 'node_id' ]
            except KeyError as exception:
                raise _exceptions.RepositoryCreationFailure(
                    self.repository_name
                ) from exception
            await _configure_repository_secrets(
                client,
                repository_owner,
                self.repository_name,
                gpg_signing_key,
                anthropic_api_key )
            await _configure_branch_protections(
                client, repository_id )
            await _configure_pages_and_deployments(
                client, repository_owner, self.repository_name )
            print( f"\nSuccessfully configured repository: {self.repository_name}" )  # noqa: E501
            print(
                f"Repository URL: https://github.com/{repository_owner}/"
                f"{self.repository_name}" )


def execute( ) -> None:
    ''' Entrypoint for CLI execution. '''
    config = (
        __.tyro.conf.EnumChoicesFromValues,
        __.tyro.conf.HelptextFromCommentsOff,
    )
    with __.warnings.catch_warnings( ):
        __.warnings.filterwarnings(
            'ignore',
            message = r'Mutable type .* is used as a default value.*',
            category = UserWarning,
            module = 'tyro.constructors._struct_spec_dataclass' )
        try: __.asyncio.run( __.tyro.cli( Cli, config = config )( ) )
        except SystemExit: raise
        except BaseException as exc:
            _scribe.error( "%s: %s", type( exc ).__name__, exc )
            raise SystemExit( 1 ) from None
