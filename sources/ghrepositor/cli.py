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


def execute( ) -> None:
    ''' Entrypoint for CLI execution. '''
    from asyncio import run
    config = (
        __.tyro.conf.HelptextFromCommentsOff,
    )
    try: run( __.tyro.cli( _main, config = config )( ) ) # pyright: ignore
    except SystemExit: raise
    except BaseException:
        # TODO: Log exception.
        raise SystemExit( 1 ) from None


async def _main( ) -> None:
    print( "Hello from ghrepositor CLI!" )
