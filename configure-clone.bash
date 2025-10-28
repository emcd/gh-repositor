#!/usr/bin/env bash

set -eu -o pipefail

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

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "Error: This script should not be sourced. Please run it directly." >&2
    return 1 2>/dev/null || exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Current directory is not in a Git repository" >&2
    exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
if [ -z "$repo_root" ]; then
    echo "Error: Could not determine Git repository root" >&2
    exit 1
fi

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
