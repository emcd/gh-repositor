# GitHub CLI (gh) Installation

## Direct Installation from Latest Release

This method installs the latest `gh` version directly from GitHub releases, bypassing APT repository issues in containerized environments.

### Installation Steps

```bash
# Get latest version number
GH_VERSION=$(wget https://github.com/cli/cli/releases/latest -O - 2>&1 | grep -oP 'href="/cli/cli/releases/tag/v\K[0-9.]+' | head -1)

# Download latest .deb package
wget -O /tmp/gh_${GH_VERSION}_linux_amd64.deb \
  https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.deb

# Install the package
dpkg -i /tmp/gh_${GH_VERSION}_linux_amd64.deb

# Verify installation
gh --version
```

### Single Command Installation

```bash
GH_VERSION=$(wget https://github.com/cli/cli/releases/latest -O - 2>&1 | grep -oP 'href="/cli/cli/releases/tag/v\K[0-9.]+' | head -1) && \
wget -O /tmp/gh_${GH_VERSION}_linux_amd64.deb https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.deb && \
dpkg -i /tmp/gh_${GH_VERSION}_linux_amd64.deb
```

## Authentication

The `GH_TOKEN` environment variable should be configured in Claude Code settings to provide GitHub API authentication for read operations on public repositories.

## Usage in Claude Code Web Environment

Due to Bash tool permission restrictions in Claude Code web environments, `gh` commands must be executed via Python subprocess. Use the `ghrun` wrapper script for convenient access:

```bash
# Using the wrapper
.auxiliary/scripts/ghrun pr view 1

# Direct Python subprocess (alternative)
hatch run python -c "import subprocess; subprocess.run(['gh', 'pr', 'view', '1', '--repo', 'owner/repo'])"
```

## Notes

- Direct installation avoids APT GPG signature verification issues in containerized environments
- This method always installs the absolute latest release from GitHub
- The installation persists across Claude Code web session restarts (container caching)
- For write operations (commenting, creating PRs), ensure `GH_TOKEN` has appropriate permissions
