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


''' Configuration management for repository creation. '''


import os
import sys
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv



@dataclass( frozen = True )
class RepositoryConfig:
    ''' Configuration for repository creation. '''
    
    github_token: str
    gpg_signing_key: str
    anthropic_api_key: str
    project_name: str
    repository_owner: Optional[ str ] = None
    
    @classmethod
    def from_environment( cls, project_name: str ) -> 'RepositoryConfig':
        ''' Create configuration from environment variables. '''
        load_dotenv( )
        
        github_token = os.environ.get( 'GITHUB_TOKEN' )
        if not github_token:
            print(
                "ERROR: GITHUB_TOKEN not found in environment",
                file = sys.stderr
            )
            sys.exit( 1 )
        
        gpg_signing_key = os.environ.get( 'GPG_SIGNING_KEY' )
        if not gpg_signing_key:
            print(
                "ERROR: GPG_SIGNING_KEY not found in environment",
                file = sys.stderr
            )
            sys.exit( 1 )
        
        anthropic_api_key = os.environ.get( 'ANTHROPIC_API_KEY' )
        if not anthropic_api_key:
            print(
                "ERROR: ANTHROPIC_API_KEY not found in environment",
                file = sys.stderr
            )
            sys.exit( 1 )
        
        repository_owner = os.environ.get( 'REPOSITORY_OWNER' )
        
        return cls(
            github_token = github_token,
            gpg_signing_key = gpg_signing_key,
            anthropic_api_key = anthropic_api_key,
            project_name = project_name,
            repository_owner = repository_owner
        )


def get_github_headers( github_token: str ) -> dict[ str, str ]:
    ''' Get standard GitHub API headers. '''
    return {
        'Authorization': f"token {github_token}",
        'Accept': 'application/vnd.github+json',
    }