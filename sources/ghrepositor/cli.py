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
from . import interfaces as _interfaces
from . import state as _state


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
            auxdata: _state.Globals,
            *posargs: __.typx.Any,
            **nomargs: __.typx.Any,
        ) -> None:
            stream = await auxdata.display.provide_stream( auxdata.exits )
            try: return await function( self, auxdata, *posargs, **nomargs )
            except _exceptions.Omnierror as exc:
                match auxdata.display.format:
                    case _interfaces.DisplayFormat.JSON:
                        error_data = dict( exc.render_as_json( ) )
                        error_message = __.json.dumps( error_data, indent = 2 )
                        print( error_message, file = stream )
                    case _interfaces.DisplayFormat.Markdown:
                        error_lines = exc.render_as_markdown( )
                        print( '\n'.join( error_lines ), file = stream )
                raise SystemExit( 1 ) from None
            except Exception as exc:
                _scribe.error( f"{function.__name__} failed: %s", exc )
                error_message = __.json.dumps( {
                    "type": "unexpected_error",
                    "message": str( exc ),
                }, indent = 2 )
                print( error_message, file = stream )
                raise SystemExit( 1 ) from None

        return wrapper
    return decorator


def _retrieve_github_token( ) -> __.Absential[ str ]:
    ''' Retrieves GitHub token from environment or gh CLI. '''
    token = __.os.environ.get( 'GITHUB_TOKEN' )
    if token: return token
    try:
        result = __.subprocess.run(
            [ 'gh', 'auth', 'token' ],
            capture_output = True,
            text = True,
            check = True,
            timeout = 5 )
    except (
        FileNotFoundError,
        __.subprocess.CalledProcessError,
        __.subprocess.TimeoutExpired,
    ):
        return __.absent
    else:
        token = result.stdout.strip( )
        if token: return token
    return __.absent


_run_command = __.funct.partial(
    __.subprocess.run,
    capture_output = True,
    text = True,
    check = True,
    timeout = 5 )


def _parse_gpg_keyring( ) -> __.Absential[ str ]:
    ''' Extracts GitHub Actions Robot GPG signing key from keyring. '''
    try:
        list_result = _run_command(
            [ 'gpg', '--list-secret-keys', '--with-subkey-fingerprints' ] )
    except (
        FileNotFoundError,
        __.subprocess.CalledProcessError,
        __.subprocess.TimeoutExpired,
    ):
        return __.absent
    else:
        lines = list_result.stdout.split( '\n' )
        key_id = None
        found_github_actions = False
        skip_next = False
        for line in lines:
            if 'Github Actions Robot' in line:
                found_github_actions = True
                skip_next = True  # Skip the "ssb" line
            elif found_github_actions:
                if skip_next and line.strip( ).startswith( 'ssb' ):
                    skip_next = False  # Next line will have the fingerprint
                elif not skip_next and line.strip( ):
                    # This should be the fingerprint line
                    key_id = line.strip( )
                    break
        if not key_id: return __.absent
    try:
        export_result = _run_command(
            [ 'gpg', '--armor', '--export-secret-subkeys', key_id ] )
    except (
        FileNotFoundError,
        __.subprocess.CalledProcessError,
        __.subprocess.TimeoutExpired,
    ):
        return __.absent
    else:
        exported_key = export_result.stdout.strip( )
        if exported_key: return exported_key
    return __.absent


def _retrieve_gpg_signing_key( ) -> __.Absential[ str ]:
    ''' Retrieves GPG signing key from environment or GPG keyring. '''
    key = __.os.environ.get( 'GPG_SIGNING_KEY' )
    if key: return key
    return _parse_gpg_keyring( )


def _retrieve_anthropic_api_key( ) -> __.Absential[ str ]:
    ''' Retrieves Anthropic API key from environment or .env file. '''
    key = __.os.environ.get( 'ANTHROPIC_API_KEY' )
    if key: return key
    env_path = __.pathlib.Path( '.env' )
    if env_path.exists( ):
        values = __.dotenv.dotenv_values( env_path )
        key = values.get( 'ANTHROPIC_API_KEY' )
        if key: return key
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
        raise _exceptions.EnvironmentConfigurationAbsence(
            'ANTHROPIC_API_KEY' )
    return github_token, gpg_signing_key, anthropic_api_key


async def _configure_repository_secrets(
    client: __.httpx.AsyncClient,
    repository_owner: str,
    repository_name: str,
    gpg_signing_key: str,
    anthropic_api_key: str,
) -> None:
    ''' Configures repository secrets. '''
    _scribe.info( "Retrieving repository public key..." )
    public_key_info = await _github.get_repository_public_key(
        client, repository_owner, repository_name )
    _scribe.info( "Adding repository secrets..." )
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
    _scribe.info( "Configuring branch protection rules..." )
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
    _scribe.info( "Configuring GitHub Pages..." )
    await _github.configure_github_pages(
        client, repository_owner, repository_name )
    _scribe.info( "Configuring deployment branch policies..." )
    deployment_policies = (
        { 'name': 'master', 'type': 'branch' },
        { 'name': 'v[0-9]*', 'type': 'tag' },
    )
    await _github.configure_deployment_policies(
        client, repository_owner, repository_name, deployment_policies )


class Cli( __.appcore_cli.Application ):
    ''' GitHub repository creation and configuration CLI. '''

    display: _state.DisplayOptions = __.dcls.field(
        default_factory = _state.DisplayOptions )

    repository_name: __.typx.Annotated[
        __.tyro.conf.Positional[ str ],
        __.tyro.conf.arg( help = "Name for new repository" ),
    ]

    async def prepare(
        self, exits: __.ctxl.AsyncExitStack
    ) -> _state.Globals:
        ''' Prepares package-specific global state. '''
        auxdata_base = await super( ).prepare( exits )
        nomargs = {
            field.name: getattr( auxdata_base, field.name )
            for field in __.dcls.fields( auxdata_base )
            if not field.name.startswith( '_' ) }
        return _state.Globals( display = self.display, **nomargs )

    @intercept_errors( )
    async def execute(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, auxdata: _state.Globals
    ) -> None:
        ''' Creates and configures GitHub repository. '''
        github_token, gpg_signing_key, anthropic_api_key = (
            _retrieve_credentials( ) )
        headers = {
            'Authorization': f"token {github_token}",
            'Accept': 'application/vnd.github+json',
        }
        async with __.httpx.AsyncClient( headers = headers ) as client:
            _scribe.info( f"Creating repository: {self.repository_name}" )
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
            _scribe.info(
                "Successfully configured repository: %s",
                self.repository_name )
            _scribe.info(
                "Repository URL: https://github.com/%s/%s",
                repository_owner, self.repository_name )


def execute( ) -> None:
    ''' Entrypoint for CLI execution. '''
    config = (
        __.tyro.conf.EnumChoicesFromValues,
        __.tyro.conf.HelptextFromCommentsOff,
    )
    try: __.asyncio.run( __.tyro.cli( Cli, config = config )( ) )
    except SystemExit: raise
    except BaseException as exc:
        _scribe.error( "%s: %s", type( exc ).__name__, exc )
        raise SystemExit( 1 ) from None
