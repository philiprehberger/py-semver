# Changelog

## 0.2.0 (2026-04-27)

- Add `expand_range(range_str)` returning the inclusive lower bound and exclusive upper bound of a caret/tilde/comparator range
- Replace 7-line import-only test with a comprehensive test suite covering `parse`, `bump`, `compare`, `is_valid`, `sort_versions`, `next_pre`, `satisfies`, and `expand_range`
- Repair malformed CHANGELOG entry from previous release

## 0.1.7 (2026-03-31)

- Standardize README to 3-badge format with emoji Support section
- Update CI checkout action to v5 for Node.js 24 compatibility
- Add GitHub issue templates, dependabot config, and PR template

## 0.1.6 (2026-03-29)

- Add pytest and mypy tool configuration to pyproject.toml

## 0.1.5 (2026-03-22)

- Add basic import test

## 0.1.4 (2026-03-19)

- Add Development section to README

## 0.1.1 (2026-03-17)

- Re-release for PyPI publishing

## 0.1.0 (2026-03-15)

- Initial release
- Parse, compare, and validate semver strings
- Bump major, minor, and patch versions
- Range matching with `>=`, `<`, `^`, and `~` operators
- Sort version string lists
- Generate next pre-release versions
