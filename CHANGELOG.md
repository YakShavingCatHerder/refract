# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- README demo GIF and `./demo/record.sh` recorder
- CI gate job so a single `CI` check can be required on PRs
- Release smoke test: install the built wheel and run CLI tests before PyPI
- GitHub Release on `v*` tags, with wheel and sdist attached
- Dependabot for GitHub Actions (PRs target `staging`)

### Changed

- CI installs `dist/*.whl` / `dist/*.tar.gz` instead of a hardcoded version
- CI uses a read-only `GITHUB_TOKEN`, concurrency (cancel stale PR runs), and job timeouts
- Release refuses a tag that does not match `pyproject.toml` `version`

### Removed

- Documented `pip install refract-venv` / `./install.sh --pip` as install recipes (Homebrew and Debian `pip3` are PEP 668-managed)

## [0.1.0] - 2026-09-11

First PyPI release. Distribution name is `refract-venv`; the command is `refract`.

### Added

- Commands: `install`, `init`, `list`, `use`, `current`, `rm`, `colorway`
- Environments stored under `~/.refract/envs/`
- bash and zsh prompt integration (`[refract:<env>]`) and colorway support
- `./install.sh` (copy to `~/.local/bin`) and `./install.sh --pipx`
- `./uninstall.sh` (leaves `~/.refract/` in place)
- CLI tests and GitHub Actions CI (macOS/Linux, Python 3.10–3.14, bash/zsh)
- Trusted Publishing to PyPI on `v*` tags that are on `main`

### Notes

- macOS and Linux only. Windows is not supported.
- Requires Python 3.10 or newer. No runtime dependencies.

[Unreleased]: https://github.com/YakShavingCatHerder/refract/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YakShavingCatHerder/refract/releases/tag/v0.1.0
