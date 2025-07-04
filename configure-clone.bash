#!/usr/bin/env bash

set -eu -o pipefail

# Check if script is being sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "Error: This script should not be sourced. Please run it directly." >&2
    return 1 2>/dev/null || exit 1
fi

# Check if current directory is in a Git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Current directory is not in a Git repository" >&2
    exit 1
fi

# Find the top of the Git repository
repo_root="$(git rev-parse --show-toplevel)"
if [ -z "$repo_root" ]; then
    echo "Error: Could not determine Git repository root" >&2
    exit 1
fi

# Check that .auxiliary/configuration exists relative to repo root
aux_config_dir="$repo_root/.auxiliary/configuration"
if [ ! -d "$aux_config_dir" ]; then
    echo "Error: .auxiliary/configuration directory not found at $aux_config_dir" >&2
    exit 1
fi

# Function to create symlink if target exists and symlink doesn't exist
create_symlink_if_needed() {
    local target_path="$1"
    local link_path="$2"
    
    if [ ! -e "$aux_config_dir/$target_path" ]; then
        echo "Warning: Target $aux_config_dir/$target_path does not exist" >&2
        return
    fi
    
    if [ -L "$repo_root/$link_path" ]; then
        # Symlink already exists, skip
        return
    elif [ -e "$repo_root/$link_path" ]; then
        echo "Warning: File or directory already exists at $repo_root/$link_path" >&2
        return
    fi
    
    # Create the symlink (will be executed from repo root via pushd)
    ln -s ".auxiliary/configuration/$target_path" "$link_path"
}

# Function to create all symlinks from repo root
create_symlinks() {
    # Set up trap to ensure we always popd
    trap 'popd >/dev/null 2>&1 || true' ERR EXIT
    
    # Change to repo root for symlink creation
    pushd "$repo_root" >/dev/null
    
    # Create symlinks
    create_symlink_if_needed "conventions.md" "CLAUDE.md"
    create_symlink_if_needed "mcp-servers.json" ".mcp.json"
    create_symlink_if_needed "claude" ".claude"
    create_symlink_if_needed "gemini" ".gemini"
    
    # Return to original directory
    popd >/dev/null
    
    # Clear the trap
    trap - ERR EXIT
}

# Execute symlink creation
create_symlinks

# my_gpg_signing_key_id="$(
#     gpg --list-secret-keys --keyid-format=long \
#     | grep --after-context 1 --extended-regexp '^uid.*Eric McDonald \(Github\)' \
#     | tail -1 | awk '{print $2}' | awk -F/ '{print $2}')"

# git config user.email 'emcd@users.noreply.github.com'
# git config user.name 'Eric McDonald'
# git config user.signingkey "${my_gpg_signing_key_id}!"
# git config commit.gpgsign true
# git config tag.gpgsign true
