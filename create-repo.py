import os
import requests
from base64 import b64encode
from nacl import encoding, public

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GPG_SIGNING_KEY = os.environ["GPG_SIGNING_KEY"]
GH_PROJECT_NAME = os.environ["GH_PROJECT_NAME"]

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

# Create an empty repository
url = "https://api.github.com/user/repos"
data = {"name": GH_PROJECT_NAME, "private": False}
response = requests.post(url, json=data, headers=headers)
response.raise_for_status()
repo_info = response.json()
repo_owner = repo_info['owner']['login']

# Get the public key for the repository
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/actions/secrets/public-key"
response = requests.get(url, headers=headers)
response.raise_for_status()
public_key_info = response.json()

# Encrypt the GPG signing key using the public key
encrypted_signing_key = encrypt(public_key_info["key"], GPG_SIGNING_KEY)

# Add the encrypted GPG signing key as a repository secret
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/actions/secrets/GHA_COMMIT_SIGNING_KEY"
data = {"encrypted_value": encrypted_signing_key, "key_id": public_key_info["key_id"]}
response = requests.put(url, json=data, headers=headers)
response.raise_for_status()

# GraphQL query to set protection rules for master and release-* branches
query = f"""
mutation {{
  masterRule: createBranchProtectionRule(input: {{
    repositoryId: "{repo_info['node_id']}",
    pattern: "master",
    requiresCommitSignatures: true
  }}) {{
    clientMutationId
  }}
  releaseRule: createBranchProtectionRule(input: {{
    repositoryId: "{repo_info['node_id']}",
    pattern: "release-*",
    requiresCommitSignatures: true
  }}) {{
    clientMutationId
  }}
}}
"""

url = "https://api.github.com/graphql"
data = {"query": query}
response = requests.post(url, json=data, headers=headers)
response.raise_for_status()

# Create GitHub Pages environment
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/environments/github-pages"
data = {
    "wait_timer": 0,
    "reviewers": [],
    "deployment_branch_policy": {
        "protected_branches": False,
        "custom_branch_policies": True,
    }
}
response = requests.put(url, json=data, headers=headers)
response.raise_for_status()

# Configure GitHub Pages to use GitHub Actions as source
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/pages"
data = {
    "source": {
        "branch": "master",  # Required but not actually used
        "path": "/",         # Required but not actually used
    },
    "build_type": "workflow"
}
response = requests.post(url, json=data, headers=headers)
response.raise_for_status()

# Set the deployment branch policy for the master branch and release tags
url = f"https://api.github.com/repos/{repo_owner}/{GH_PROJECT_NAME}/environments/github-pages/deployment-branch-policies"
data = {"name": "master"}
for data in ( {"name": "master"}, {"name": "v*"} ):
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

print("Successfully configured the repository.")
