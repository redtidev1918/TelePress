# Contributing to TelePress

Thanks for improving TelePress. Small, focused pull requests with tests and clear
commit messages are easiest to review and release.

## Development setup

TelePress supports Python 3.10 and newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --editable ".[dev]"
```

Run the same core checks used by CI:

```bash
python -m pytest --cov
python -m build
python -m twine check dist/*
```

Tests must not require real Telegraph or image-host credentials. Mock network
boundaries and use temporary files for filesystem behavior.

## Commit messages

The release workflow uses
[Conventional Commits](https://www.conventionalcommits.org/) to calculate the
next version and generate release notes.

```text
fix: clean temporary files when publishing fails
feat: add a new image host
docs: document custom API configuration
refactor: simplify gallery pagination
feat!: remove a deprecated public method
```

- `fix:` produces a patch release.
- `feat:` produces a minor release.
- `type!:` or a `BREAKING CHANGE:` footer marks a breaking release.
- Documentation, test, build, and maintenance commits appear in history but do
  not force a release by themselves.

Keep the subject imperative, concise, and scoped to one logical change.

## Pull requests

Before requesting review:

- Add or update tests for behavior changes.
- When **user-facing behavior changes**, update the corresponding canonical docs.
  The README is **not** the full documentation mirror; do not force every feature
  into `README.md` / `README.en.md`.
- Only update the README for the following:
  - install instructions change
  - core product positioning changes
  - quick-start commands change
  - a top-level capability changes (for example a new publishing plane entry point)
- Do not edit `src/telepress/version.py` or `CHANGELOG.md` for ordinary pull
  requests; the release pull request manages them.
- Confirm the complete local test suite passes.
- Explain compatibility or security implications in the pull request body.

Canonical documentation lives under `docs/`:

| Topic | Canonical docs |
| --- | --- |
| Getting started / install | `docs/getting-started.md` |
| Configuration | `docs/configuration.md` |
| REST API contracts | `docs/api/*.md` |
| Media proxy / image hosts | `docs/media/*.md` |
| Python API / CLI | `docs/python-api.md`, `docs/cli.md` |
| Architecture | `docs/architecture/*.md` |
| Operations / current state | `docs/operations/*.md` |
| Releasing | `docs/en/development/releasing.md` |

English mirrors live under `docs/en/`. Update both languages when user-facing
behavior changes.

See [docs/en/development/releasing.md](docs/en/development/releasing.md) for
maintainer release operations.
