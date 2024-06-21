* Setup environment for publishing releases.
  Provides separate set of permissions for publication
  and can be additional claim on JWT from OIDC auth workflow.
  https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/

* Replace GPG signing key with use of Github GraphQL mutation
  ``createCommitOnBranch`` to generate a Github-signed commit.
  https://github.com/actions/runner/issues/667#issuecomment-1826802554
