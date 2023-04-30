#!/usr/bin/env bash

set -eu -o pipefail

if [[ -z "$1" ]]; then
    echo 1>&2 'ERROR: Must supply project name.'
    exit 1
fi

export GH_PROJECT_NAME="$1"

export GITHUB_TOKEN="$(gh auth token)"

gha_gpg_signing_key_id="$(
    gpg --list-secret-keys --with-subkey-fingerprints \
    | grep --after-context 2 --extended-regexp '^uid.*Github Actions Robot' \
    | tail -1 | awk '{print $1}')"
export GPG_SIGNING_KEY="$(
    gpg --armor --export-secret-subkeys "${gha_gpg_signing_key_id}")"

local -r venv_name='repo-creator-venv'
rm --force --recursive "${venv_name}"
python3 -m venv "${venv_name}"
source "${venv_name}/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install pynacl requests

python3 create-repo.py
