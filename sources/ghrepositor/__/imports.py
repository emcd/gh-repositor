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


''' Common imports used throughout the package. '''

# ruff: noqa: F401


import asyncio
import base64
import collections.abc as   cabc
import contextlib as        ctxl
import functools as         funct
import json
import os
import pathlib
import subprocess
import types
import warnings

import httpx
import                      nacl

import typing_extensions as typx

import appcore.cli as       appcore_cli
import                      dotenv
# --- BEGIN: Injected by Copier ---
import dynadoc as           ddoc
import frigid as            immut
import tyro
# --- END: Injected by Copier ---

from logging import getLogger as acquire_scribe

# --- BEGIN: Injected by Copier ---
from absence import Absential, absent, is_absent
from appcore.state import Globals
# --- END: Injected by Copier ---

standard_tyro_class = tyro.conf.configure( tyro.conf.OmitArgPrefixes )
