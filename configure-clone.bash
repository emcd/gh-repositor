#!/usr/bin/env bash

set -eu -o pipefail

# my_gpg_signing_key_id="$(
#     gpg --list-secret-keys --keyid-format=long \
#     | grep --after-context 1 --extended-regexp '^uid.*Eric McDonald \(Github\)' \
#     | tail -1 | awk '{print $2}' | awk -F/ '{print $2}')"

# git config user.email 'emcd@users.noreply.github.com'
# git config user.name 'Eric McDonald'
# git config user.signingkey "${my_gpg_signing_key_id}!"
# git config commit.gpgsign true
# git config tag.gpgsign true
