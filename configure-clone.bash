#!/usr/bin/env bash

set -eu -o pipefail

# Parse command line arguments
force_mode=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            force_mode=true
            shift
            ;;
        *)
            echo "Error: Unknown option $1" >&2
            echo "Usage: $0 [--force]" >&2
            exit 1
            ;;
    esac
done

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

# Function to download project documentation guides
download_instructions() {
    local instructions_dir="$repo_root/.auxiliary/instructions"
    local base_url="https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common"
    local files=("practices.rst" "style.rst" "nomenclature.rst" "nomenclature-germanic.rst" "tests.rst")

    # Create instructions directory if it doesn't exist
    mkdir -p "$instructions_dir"

    echo "Downloading project documentation guides to .auxiliary/instructions/"

    local success_count=0
    for file in "${files[@]}"; do
        local url="$base_url/$file"
        local output_path="$instructions_dir/$file"

        if curl --fail --silent --location --output "$output_path" "$url"; then
            if [ -s "$output_path" ]; then
                echo "  ✓ Downloaded $file ($(wc -c < "$output_path") bytes)"
                success_count=$((success_count + 1))
            else
                echo "  ✗ Downloaded $file but file is empty" >&2
                rm -f "$output_path"
            fi
        else
            echo "  ✗ Failed to download $file" >&2
        fi
    done

    if [ $success_count -eq ${#files[@]} ]; then
        echo "Successfully downloaded all ${#files[@]} documentation guides"
    else
        echo "Warning: Only downloaded $success_count of ${#files[@]} documentation guides" >&2
    fi
}

# Execute symlink creation
create_symlinks

# Download project documentation guides
download_instructions

# Install Git LFS from repo root
(
    cd "$repo_root"
    git_hooks_dir="$(git rev-parse --git-dir)/hooks"
    pre_push_hook="$git_hooks_dir/pre-push"

    if [ -f "$pre_push_hook" ] && [ "$force_mode" = false ]; then
        echo "Warning: Git pre-push hook already exists at $pre_push_hook" >&2
        echo "Warning: Skipping 'git lfs install' to avoid overwriting existing hook" >&2
        echo "Warning: Use --force option to override this behavior" >&2
    else
        if [ "$force_mode" = true ]; then
            git lfs update --force
        else
            git lfs install
        fi
    fi
)

# Check if repo contains pyproject.toml and run pre-commit install
if [ -f "$repo_root/pyproject.toml" ]; then
    (
        cd "$repo_root"
        git_hooks_dir="$(git rev-parse --git-dir)/hooks"
        pre_commit_hook="$git_hooks_dir/pre-commit"

        if [ -f "$pre_commit_hook" ] && [ "$force_mode" = false ]; then
            echo "Warning: Git pre-commit hook already exists at $pre_commit_hook" >&2
            echo "Warning: Skipping pre-commit hook installation to avoid overwriting existing hook" >&2
            echo "Warning: Use --force option to override this behavior" >&2
        else
            hatch --env develop run pre-commit install --config .auxiliary/configuration/pre-commit.yaml
        fi
    )
fi
