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


''' GitHub API client for repository creation and management. '''


from base64 import b64encode
from typing import Any, Dict

import requests
from nacl import encoding, public

from .config import RepositoryConfig, get_github_headers


class GitHubRepositoryManager:
    ''' Manager for GitHub repository operations. '''
    
    def __init__( self, config: RepositoryConfig ):
        self.config = config
        self.headers = get_github_headers( config.github_token )
        self.session = requests.Session( )
        self.session.headers.update( self.headers )
    
    def encrypt_secret( self, public_key: str, secret_value: str ) -> str:
        ''' Encrypt a secret value using the repository's public key. '''
        public_key_obj = public.PublicKey(
            public_key.encode( "utf-8" ), encoding.Base64Encoder( )
        )
        sealed_box = public.SealedBox( public_key_obj )
        encrypted = sealed_box.encrypt( secret_value.encode( "utf-8" ) )
        return b64encode( encrypted ).decode( "utf-8" )
    
    def create_repository( self, private: bool = False ) -> Dict[ str, Any ]:
        ''' Create a new GitHub repository. '''
        url = 'https://api.github.com/user/repos'
        data = {
            'name': self.config.project_name,
            'private': private
        }
        
        response = self.session.post( url, json = data )
        response.raise_for_status( )
        return response.json( )
    
    def get_public_key(
        self, repo_owner: str, repo_name: str
    ) -> Dict[ str, str ]:
        ''' Get the public key for repository secrets. '''
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/public-key"
        response = self.session.get( url )
        response.raise_for_status( )
        return response.json( )
    
    def add_repository_secret(
        self,
        repo_owner: str,
        repo_name: str,
        secret_name: str,
        secret_value: str,
        public_key_info: Dict[ str, str ]
    ) -> None:
        ''' Add an encrypted secret to the repository. '''
        encrypted_value = self.encrypt_secret(
            public_key_info[ 'key' ], secret_value
        )
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/{secret_name}"
        data = {
            'encrypted_value': encrypted_value,
            'key_id': public_key_info[ 'key_id' ]
        }
        
        response = self.session.put( url, json = data )
        response.raise_for_status( )
    
    def create_branch_protection_rules(
        self, repo_info: Dict[ str, Any ]
    ) -> None:
        '''
        Create branch protection rules for master and release-* branches.
        '''
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
        response = self.session.post( url, json = data )
        response.raise_for_status( )
    
    def create_github_pages_environment(
        self, repo_owner: str, repo_name: str
    ) -> None:
        ''' Create GitHub Pages environment. '''
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/environments/github-pages"
        data = {
            'wait_timer': 0,
            'reviewers': [ ],
            'deployment_branch_policy': {
                'protected_branches': False,
                'custom_branch_policies': True,
            }
        }
        
        response = self.session.put( url, json = data )
        response.raise_for_status( )
    
    def configure_github_pages(
        self, repo_owner: str, repo_name: str
    ) -> None:
        ''' Configure GitHub Pages to use GitHub Actions as source. '''
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pages"
        data = {
            'source': {
                'branch': 'master',
                'path': '/',
            },
            'build_type': 'workflow'
        }
        
        response = self.session.post( url, json = data )
        response.raise_for_status( )
    
    def set_deployment_branch_policies(
        self, repo_owner: str, repo_name: str
    ) -> None:
        '''
        Set deployment branch policies for master branch and release tags.
        '''
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/environments/github-pages/deployment-branch-policies"
        
        policies = [
            { 'name': 'master', 'type': 'branch' },
            { 'name': 'v[0-9]*', 'type': 'tag' },
        ]
        
        for policy in policies:
            response = self.session.post( url, json = policy )
            response.raise_for_status( )
    
    def add_standard_secrets( self, repo_owner: str, repo_name: str ) -> None:
        ''' Add standard secrets to the repository. '''
        public_key_info = self.get_public_key( repo_owner, repo_name )
        
        secrets = [
            ( 'GHA_COMMIT_SIGNING_KEY', self.config.gpg_signing_key ),
            ( 'ANTHROPIC_API_KEY', self.config.anthropic_api_key ),
        ]
        
        for secret_name, secret_value in secrets:
            self.add_repository_secret(
                repo_owner, repo_name, secret_name, secret_value,
                public_key_info
            )