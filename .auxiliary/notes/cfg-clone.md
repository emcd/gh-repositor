# Plan: Port configure-clone.bash to CLI Subcommand

## Overview
Port the `configure-clone.bash` script to a Python CLI subcommand called `configure-clone` (or `config-clone`). This script sets up Git LFS and pre-commit hooks for a cloned repository.

## Current Functionality Analysis

### What configure-clone.bash Does:
1. **Validates environment**
   - Ensures it's not being sourced (must be executed)
   - Verifies current directory is in a Git repository
   - Finds the Git repository root

2. **Git LFS setup**
   - Runs `git lfs install` (or `git lfs update --force` with `--force` flag)
   - Checks if pre-push hook already exists before overwriting
   - Skips if hook exists (unless `--force` is used)

3. **Pre-commit hooks setup** (only if `pyproject.toml` exists)
   - Installs pre-commit hooks using hatch
   - Checks if pre-commit hook already exists before overwriting
   - Skips if hook exists (unless `--force` is used)
   - Uses custom config path: `.auxiliary/configuration/pre-commit.yaml`

### Command-line Interface:
- Optional `--force` flag to overwrite existing hooks

## Proposed Design

### CLI Structure
```python
# Usage: ghrepositor configure-clone [OPTIONS]
class ConfigureClone(Subcommand):
    force: bool = False  # --force flag to overwrite existing hooks
```

### Implementation Approach

#### 1. Use Tyro Subcommands
Currently `ghrepositor` has a single command. We'll need to:
- Refactor `Cli` class to support subcommands
- Create `CreateRepository` subcommand (current functionality)
- Create `ConfigureClone` subcommand (new functionality)

#### 2. File Structure
```
sources/ghrepositor/
├── cli.py              # Main CLI entry point with subcommand routing
├── commands/
│   ├── __init__.py
│   ├── __.py           # Re-exporter: `from ..__ import *` + parent imports
│   ├── create.py       # CreateRepository command (current execute() logic)
│   └── configure.py    # ConfigureClone command (new)
├── github.py           # (unchanged)
├── exceptions.py       # (add new exceptions for configure-clone)
├── interfaces.py       # (unchanged)
└── state.py            # (unchanged)
```

**Note on commands/__.py**: This module provides a clean import interface for command modules, containing `from ..__ import *` plus any other imports from the parent package. This avoids `from ..some_module import` spaghetti in actual command modules.

#### 3. New Exceptions Needed
```python
# In exceptions.py
class GitRepositoryAbsence(Omnierror):
    """Raised when not in a Git repository."""

class GitLfsInavailability(Omnierror):
    """Raised when git-lfs is not installed."""

class PreCommitInavailability(Omnierror):
    """Raised when pre-commit is not available."""

class HookInstallationFailure(Omnierror):
    """Raised when hook installation fails."""
```

#### 4. Core Logic (configure.py)

**Repository validation:**
```python
def _validate_git_repository() -> pathlib.Path:
    """Ensures we're in a Git repository and returns root path."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            capture_output=True, check=True)
        # Get repository root
        root_result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, check=True, text=True)
        return pathlib.Path(root_result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise GitRepositoryAbsence()
```

**Git LFS installation:**
```python
async def _install_git_lfs(repo_root: pathlib.Path, force: bool) -> None:
    """Installs Git LFS hooks."""
    git_dir = repo_root / '.git'
    pre_push_hook = git_dir / 'hooks' / 'pre-push'

    if pre_push_hook.exists() and not force:
        # Log warning about existing hook
        return

    cmd = ['git', 'lfs', 'update', '--force'] if force else ['git', 'lfs', 'install']
    try:
        subprocess.run(cmd, cwd=repo_root, check=True)
    except subprocess.CalledProcessError as exc:
        raise HookInstallationFailure('git-lfs') from exc
```

**Pre-commit installation:**
```python
async def _install_precommit_hooks(repo_root: pathlib.Path, force: bool) -> None:
    """Installs pre-commit hooks using hatch."""
    if not (repo_root / 'pyproject.toml').exists():
        return  # Skip if not a Python project

    git_dir = repo_root / '.git'
    pre_commit_hook = git_dir / 'hooks' / 'pre-commit'

    if pre_commit_hook.exists() and not force:
        # Log warning about existing hook
        return

    cmd = [
        'hatch', '--env', 'develop', 'run',
        'pre-commit', 'install',
        '--config', '.auxiliary/configuration/pre-commit.yaml'
    ]
    try:
        subprocess.run(cmd, cwd=repo_root, check=True)
    except subprocess.CalledProcessError as exc:
        raise HookInstallationFailure('pre-commit') from exc
```

**Main execute method:**
```python
@intercept_errors()
async def execute(self, auxdata: _state.Globals) -> None:
    """Configures Git hooks for a cloned repository."""
    repo_root = _validate_git_repository()

    _scribe.info("Configuring Git LFS...")
    await _install_git_lfs(repo_root, self.force)

    _scribe.info("Installing pre-commit hooks...")
    await _install_precommit_hooks(repo_root, self.force)

    _scribe.info("Repository configuration complete")
```

## Tyro Subcommand Integration

### Updated cli.py Structure
```python
import tyro
from typing import Annotated, Union

from . import commands

# Define the union of all subcommands
Commands = Annotated[
    Union[
        Annotated[commands.CreateGhRepository, tyro.conf.subcommand(name="create-gh-repository")],
        Annotated[commands.ConfigureClone, tyro.conf.subcommand(name="configure-clone")],
    ],
    tyro.conf.subcommand()
]

def execute() -> None:
    """Entrypoint for CLI execution."""
    config = (
        __.tyro.conf.EnumChoicesFromValues,
        __.tyro.conf.HelptextFromCommentsOff,
    )
    try:
        command = tyro.cli(Commands, config=config)
        __.asyncio.run(command())
    except SystemExit:
        raise
    except BaseException as exc:
        _scribe.error("%s: %s", type(exc).__name__, exc)
        raise SystemExit(1) from None
```

## Migration Strategy

### Phase 1: Refactor existing code
1. Move current `Cli.execute()` logic to `commands/create.py` as `CreateGhRepository` command
2. Update `cli.py` to use tyro subcommands
3. Ensure existing functionality still works (now as `ghrepositor create-gh-repository`)
4. Update tests (if any)

### Phase 2: Implement configure-clone
1. Create `commands/configure.py` with `ConfigureClone` command
2. Add new exception types
3. Implement Git repository validation
4. Implement Git LFS installation
5. Implement pre-commit hook installation

### Phase 3: Testing & Polish
1. Test both commands independently
2. Test error cases (not in repo, hooks already exist, missing tools)
3. Update documentation
4. Add output formatting (JSON/Markdown) for configure-clone

## Design Decisions

1. **Command naming**: `create-gh-repository` and `configure-clone`
   - **Rationale**: Explicit, self-documenting names. `create-gh-repository` clarifies it's GitHub-specific, `configure-clone` matches bash script name.

2. **Where to run**: Match existing bash behavior (work from anywhere in repo)
   - **Rationale**: Convenience - users shouldn't need to cd to repo root first.

3. **Async vs Sync**: Use `async` for consistency
   - **Rationale**: Consistent with create command, even though subprocess calls are blocking. Maintains uniform async/await pattern across all commands.

4. **Output format**: Yes, should render all formats that the CLI does (JSON/Markdown)
   - **Rationale**: Consistency across all commands. Output structure:
     ```json
     {
       "status": "success",
       "repository_root": "/path/to/repo",
       "hooks_installed": {
         "git_lfs": true,
         "pre_commit": true
       },
       "warnings": []
     }
     ```

5. **Working directory**: Find repo root but run commands there (no directory change in CLI)
   - **Rationale**: Preserve user's current directory while ensuring commands run in correct context.

## Compatibility Notes

- Bash script can be kept for backward compatibility
- Eventually could print deprecation warning pointing to new CLI
- Or keep both (bash for quick setup, Python CLI for programmatic use)

## Estimated Complexity

- **Refactoring to subcommands**: Medium (need to preserve all existing behavior)
- **Implementing configure-clone**: Low (straightforward subprocess calls)
- **Testing**: Medium (need to test Git hooks, LFS, pre-commit interaction)

## Benefits of Python Implementation

1. **Consistency**: Same CLI interface as create command
2. **Error handling**: Better structured error messages (JSON/Markdown)
3. **Type safety**: Checked by Pyright
4. **Testability**: Easier to unit test than bash
5. **Cross-platform**: Better Windows support (if needed)
6. **Integration**: Could be composed with create command in future

## Implementation Checklist

When ready to implement, follow these phases:

### Phase 1: Refactor to Subcommands
- [ ] Create `commands/` subpackage with `__init__.py` and `__.py`
- [ ] Move current repository creation logic to `commands/create.py` as `CreateGhRepository` command
- [ ] Update `cli.py` to use tyro subcommands
- [ ] Test that `ghrepositor create-gh-repository` works identically to old behavior
- [ ] Update any documentation/examples

### Phase 2: Implement Configure-Clone
- [ ] Add new exception types to `exceptions.py`
- [ ] Create `commands/configure.py` with `ConfigureClone` command
- [ ] Implement repository validation logic
- [ ] Implement Git LFS hook installation
- [ ] Implement pre-commit hook installation
- [ ] Add output formatting (JSON/Markdown)
- [ ] Test with various scenarios (existing hooks, missing tools, etc.)

### Phase 3: Polish & Documentation
- [ ] Add comprehensive error messages
- [ ] Test both commands end-to-end
- [ ] Update README with new command structure
- [ ] Consider deprecation path for bash script (if desired)
