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


''' Family of exceptions for package API. '''


from . import __


class Omniexception( __.immut.exceptions.Omniexception ):
    ''' Base for all exceptions raised by package API. '''


class Omnierror( Omniexception, Exception ):
    ''' Base for error exceptions raised by package API. '''


class EnvironmentConfigurationAbsence( Omnierror, RuntimeError ):
    ''' Environment configuration variable absence. '''

    def __init__( self, variable_name: str ) -> None:
        super( ).__init__(
            f"{variable_name} environment variable not set." )


class GitHubAPIFailure( Omnierror, RuntimeError ):
    ''' GitHub API request failure. '''


class RepositoryCreationFailure( GitHubAPIFailure ):
    ''' Repository creation failure. '''

    def __init__(
        self,
        repository_name: str,
        status_code: __.Absential[ int ] = __.absent,
        response_text: __.Absential[ str ] = __.absent,
    ) -> None:
        message = f"Cannot create repository '{repository_name}'"
        if (
            not __.is_absent( status_code )
            and not __.is_absent( response_text )
        ):
            message = f"{message}: {status_code} - {response_text}"
        message = f"{message}."
        super( ).__init__( message )


class PublicKeyRetrievalFailure( GitHubAPIFailure ):
    ''' Public key retrieval failure. '''

    def __init__(
        self,
        repository_owner: str,
        repository_name: str,
        status_code: __.Absential[ int ] = __.absent,
    ) -> None:
        message = (
            f"Cannot retrieve public key for {repository_owner}/"
            f"{repository_name}" )
        if not __.is_absent( status_code ):
            message = f"{message}: {status_code}"
        message = f"{message}."
        super( ).__init__( message )


class SecretAdditionFailure( GitHubAPIFailure ):
    ''' Secret addition failure. '''

    def __init__(
        self,
        secret_name: str,
        status_code: __.Absential[ int ] = __.absent,
    ) -> None:
        message = f"Cannot add secret '{secret_name}'"
        if not __.is_absent( status_code ):
            message = f"{message}: {status_code}"
        message = f"{message}."
        super( ).__init__( message )


class PublicKeyDecodingFailure( GitHubAPIFailure ):
    ''' Public key decoding failure. '''

    def __init__( self, public_key_prefix: str ) -> None:
        super( ).__init__(
            f"Invalid public key format: {public_key_prefix}..." )


class SecretValueEncryptionFailure( GitHubAPIFailure ):
    ''' Secret value encryption failure. '''

    def __init__( self ) -> None:
        super( ).__init__( "Cannot encrypt secret value." )


class PublicKeyInformationAbsence( GitHubAPIFailure ):
    ''' Public key information field absence. '''

    def __init__( self, field_name: str ) -> None:
        super( ).__init__(
            f"Public key information missing '{field_name}' field." )


class BranchProtectionFailure( GitHubAPIFailure ):
    ''' Branch protection configuration failure. '''

    def __init__(
        self,
        branch_pattern: str,
        status_code: __.Absential[ int ] = __.absent,
    ) -> None:
        message = f"Cannot configure branch protection for '{branch_pattern}'"
        if not __.is_absent( status_code ):
            message = f"{message}: {status_code}"
        message = f"{message}."
        super( ).__init__( message )


class PagesEnvironmentCreationFailure( GitHubAPIFailure ):
    ''' GitHub Pages environment creation failure. '''

    def __init__( self, status_code: __.Absential[ int ] = __.absent ) -> None:
        message = "Cannot create GitHub Pages environment"
        if not __.is_absent( status_code ):
            message = f"{message}: {status_code}"
        message = f"{message}."
        super( ).__init__( message )


class PagesBuildConfigurationFailure( GitHubAPIFailure ):
    ''' GitHub Pages build configuration failure. '''

    def __init__( self, status_code: __.Absential[ int ] = __.absent ) -> None:
        message = "Cannot configure GitHub Pages build type"
        if not __.is_absent( status_code ):
            message = f"{message}: {status_code}"
        message = f"{message}."
        super( ).__init__( message )


class DeploymentPolicyConfigurationFailure( GitHubAPIFailure ):
    ''' Deployment policy configuration failure. '''

    def __init__(
        self,
        policy: __.cabc.Mapping[ str, str ],
        status_code: __.Absential[ int ] = __.absent,
    ) -> None:
        message = f"Cannot configure deployment policy {policy}"
        if not __.is_absent( status_code ):
            message = f"{message}: {status_code}"
        message = f"{message}."
        super( ).__init__( message )
