#!/usr/bin/env bash

set -eu -o pipefail

export GH_PROJECT_NAME="$1"

export GITHUB_TOKEN="$(gh auth token)"

gha_gpg_signing_key_id="$(
    gpg --list-secret-keys --with-subkey-fingerprints \
    | grep --after-context 2 --extended-regexp '^uid.*Github Actions Robot' \
    | tail -1 | awk '{print $1}')"
export GPG_SIGNING_KEY="$(
    gpg --armor --export-secret-subkeys "${gha_gpg_signing_key_id}")"

python3 create-repo.py
