# Automated Releases

**Language / 语言:** English · [中文](../../development/releasing.md)

TelePress uses release-please + ReleaseGraph:

```text
Conventional commits
        ↓
Release Please pull request
        ↓ maintainer review and merge
Git tag + GitHub Release
        ↓
Build and metadata verification
        ↓
PyPI Trusted Publishing + GitHub assets
        ↓
post-release-docs（refresh download page + rebuild Pages）
```

## Release flow

1. Merge Conventional Commits into `master`.
2. Release workflow creates/updates a release PR.
3. Review the version and `CHANGELOG.md`, merge the release PR.
4. Release Please creates the tag and GitHub Release.
5. The workflow builds the wheel + sdist, verifies metadata, publishes PyPI.
6. `post-release-docs` refreshes the download page and rebuilds Pages.

No local tag or `twine upload` is needed.

## One-time repository setup

- Allow Actions to create pull requests and request write permissions.
- Create a `pypi` GitHub environment.
- Configure PyPI Trusted Publisher: owner `redtidev1918`, repo `TelePress` (the canonical GitHub repository name; case-sensitive),
  workflow `release.yml`, environment `pypi`.
- Configure `RELEASE_PLEASE_TOKEN` (a fine-grained PAT with Contents / Pull requests / Issues read and write): the release PR is then authored by a real account, so CI actually triggers. Without it the author is `github-actions[bot]`, GitHub holds every run the PR triggers, and that run is finalised as a failure on merge even though CI never ran. See the [ReleaseGraph callers doc](https://github.com/redtidev1918/releasegraph/blob/main/docs/en/callers.md).

If publishing fails with `invalid-publisher`, verify these four values in the
PyPI trusted publisher settings. The repository field must use the canonical
`TelePress`, not lowercase `telepress`. After correcting it, resume the same
version through the release workflow's manual repair.

## Version policy

| Commit | Effect |
| --- | --- |
| `fix:` | patch (`0.14.0 → 0.14.1`) |
| `feat:` | minor (`0.14.x → 0.15.0`) |
| `feat!:` / `BREAKING CHANGE:` | minor before 1.0, major after |
| `docs:` / `test:` / `chore:` | no standalone release |

Exceptional versions can use a `Release-As:` footer.

## Failure recovery

- Fix CI before merging, then wait for the PR to update.
- If the release build / PyPI job fails after the GitHub Release exists, fix
  external config and rerun failed jobs.
- PyPI versions are immutable; never delete or reuse a published version.
- Do not manually move or overwrite release-please tags.

## Automation files

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.github/workflows/update-download-page.yml`
- `.github/workflows/static.yml`
- `release-please-config.json`, `.release-please-manifest.json`
