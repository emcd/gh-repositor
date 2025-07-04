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


''' High-level repository creation and configuration. '''


import os
from typing import Dict, Any, Optional

from .auth import get_github_token, get_gpg_signing_key
from .config import RepositoryConfig
from .github import GitHubRepositoryManager


class RepositoryCreator:
    ''' High-level repository creation and configuration manager. '''
    
    def __init__( self, project_name: str, private: bool = False ):
        self.project_name = project_name
        self.private = private
        self.config: Optional[ RepositoryConfig ] = None
        self.github_manager: Optional[ GitHubRepositoryManager ] = None
    
    def setup_configuration( self, use_environment: bool = True ) -> None:
        ''' Set up configuration for repository creation. '''
        if use_environment:
            # Try to get configuration from environment first
            self.config = RepositoryConfig.from_environment(
                self.project_name
            )
        else:
            # Get GitHub token and GPG key directly
            github_token = get_github_token( )
            gpg_key = get_gpg_signing_key( )
            
            # Get Anthropic API key from environment
            anthropic_api_key = os.environ.get( 'ANTHROPIC_API_KEY' )
            if not anthropic_api_key:
                msg = "ANTHROPIC_API_KEY environment variable is required"
                raise ValueError( msg )
            
            self.config = RepositoryConfig(
                github_token = github_token,
                gpg_signing_key = gpg_key,
                anthropic_api_key = anthropic_api_key,
                project_name = self.project_name
            )
        
        self.github_manager = GitHubRepositoryManager( self.config )
    
    def create_repository( self ) -> Dict[ str, Any ]:
        ''' Create a new GitHub repository. '''
        if not self.github_manager:
            msg = "Configuration not set up. Call setup_configuration() first."
            raise RuntimeError( msg )
        
        print( f"Creating repository: {self.project_name}" )
        repo_info = self.github_manager.create_repository( self.private )
        
        print( f"Repository created successfully: {repo_info['html_url']}" )
        return repo_info
    
    def configure_repository( self, repo_info: Dict[ str, Any ] ) -> None:
        '''
        Configure the repository with secrets, branch protection,
        and GitHub Pages.
        '''
        if not self.github_manager:
            msg = "Configuration not set up. Call setup_configuration() first."
            raise RuntimeError( msg )
        
        repo_owner = repo_info[ 'owner' ][ 'login' ]
        repo_name = repo_info[ 'name' ]
        
        print( "Adding repository secrets..." )
        self.github_manager.add_standard_secrets( repo_owner, repo_name )
        
        print( "Creating branch protection rules..." )
        self.github_manager.create_branch_protection_rules( repo_info )
        
        print( "Setting up GitHub Pages environment..." )
        self.github_manager.create_github_pages_environment(
            repo_owner, repo_name
        )
        
        print( "Configuring GitHub Pages..." )
        self.github_manager.configure_github_pages( repo_owner, repo_name )
        
        print( "Setting deployment branch policies..." )
        self.github_manager.set_deployment_branch_policies(
            repo_owner, repo_name
        )
        
        print( "Repository configuration completed successfully!" )
    
    def create_and_configure_repository( self ) -> Dict[ str, Any ]:
        ''' Create and fully configure a new GitHub repository. '''
        if not self.config:
            self.setup_configuration( )
        
        repo_info = self.create_repository( )
        self.configure_repository( repo_info )
        
        return repo_info


def create_repository(
    project_name: str, private: bool = False
) -> Dict[ str, Any ]:
    ''' Create and configure a new GitHub repository. '''
    creator = RepositoryCreator( project_name, private )
    return creator.create_and_configure_repository( )