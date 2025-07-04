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


''' Authentication and GPG key management for repository creation. '''


import subprocess
import sys
from typing import Optional



def get_github_token( ) -> str:
    ''' Get GitHub token using gh CLI. '''
    try:
        result = subprocess.run(
            [ 'gh', 'auth', 'token' ],  # noqa: S607
            capture_output = True,
            text = True,
            check = True
        )
        return result.stdout.strip( )
    except subprocess.CalledProcessError as exc:
        print( f"ERROR: Failed to get GitHub token: {exc}", file = sys.stderr )
        sys.exit( 1 )
    except FileNotFoundError:
        print(
            "ERROR: gh CLI not found. Please install GitHub CLI.",
            file = sys.stderr
        )
        sys.exit( 1 )


def get_gpg_signing_key( uid_pattern: str = "Github Actions Robot" ) -> str:
    ''' Get GPG signing key for the specified UID pattern. '''
    try:
        # Get the key ID for the specified UID pattern
        result = subprocess.run(
            [ 'gpg', '--list-secret-keys', '--with-subkey-fingerprints' ],  # noqa: S607
            capture_output = True,
            text = True,
            check = True
        )
        
        lines = result.stdout.split( '\n' )
        key_id = None
        
        for i, line in enumerate( lines ):
            if "uid" in line and uid_pattern in line:
                # Look for the next line with a key fingerprint
                for j in range( i + 1, len( lines ) ):
                    if lines[ j ].strip( ).startswith( ( 'ssb', 'sub' ) ):
                        # Extract the key ID from the line
                        parts = lines[ j ].split( )
                        if len( parts ) >= 2:  # noqa: PLR2004
                            key_id = parts[ 1 ]
                            break
                break
        
        if not key_id:
            print(
                f"ERROR: Could not find GPG key for UID pattern: "
                f"{uid_pattern}",
                file = sys.stderr
            )
            sys.exit( 1 )
        
        # Export the secret subkey
        result = subprocess.run(  # noqa: S603
            [ 'gpg', '--armor', '--export-secret-subkeys', key_id ],  # noqa: S607
            capture_output = True,
            text = True,
            check = True
        )
        
        return result.stdout.strip( )
        
    except subprocess.CalledProcessError as exc:
        print(
            f"ERROR: Failed to get GPG signing key: {exc}",
            file = sys.stderr
        )
        sys.exit( 1 )
    except FileNotFoundError:
        print( "ERROR: gpg not found. Please install GPG.", file = sys.stderr )
        sys.exit( 1 )


def setup_authentication(
    project_name: str, uid_pattern: Optional[ str ] = None
) -> tuple[ str, str ]:
    ''' Set up authentication by getting GitHub token and GPG key. '''
    github_token = get_github_token( )
    gpg_key = get_gpg_signing_key( uid_pattern or "Github Actions Robot" )
    
    return github_token, gpg_key