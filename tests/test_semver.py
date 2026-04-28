"""Tests for philiprehberger_semver."""

from __future__ import annotations

import pytest

from philiprehberger_semver import (
    Version,
    bump,
    compare,
    expand_range,
    is_valid,
    next_pre,
    parse,
    satisfies,
    sort_versions,
)


class TestParse:
    def test_basic(self):
        v = parse("1.2.3")
        assert (v.major, v.minor, v.patch) == (1, 2, 3)
        assert v.pre == ""
        assert v.build == ""

    def test_v_prefix(self):
        v = parse("v1.2.3")
        assert v.major == 1

    def test_pre_release(self):
        v = parse("1.2.3-rc.1")
        assert v.pre == "rc.1"

    def test_with_build_metadata(self):
        v = parse("1.2.3+build.7")
        assert v.build == "build.7"

    def test_pre_and_build(self):
        v = parse("1.2.3-alpha.1+ci.42")
        assert v.pre == "alpha.1"
        assert v.build == "ci.42"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse("not.a.version")


class TestBump:
    def test_major(self):
        assert bump("1.2.3", "major") == "2.0.0"

    def test_minor(self):
        assert bump("1.2.3", "minor") == "1.3.0"

    def test_patch(self):
        assert bump("1.2.3", "patch") == "1.2.4"

    def test_strips_pre(self):
        assert bump("1.2.3-rc.1", "patch") == "1.2.4"

    def test_invalid_part(self):
        with pytest.raises(ValueError):
            bump("1.2.3", "build")


class TestCompare:
    def test_lt(self):
        assert compare("1.0.0", "2.0.0") == -1

    def test_eq(self):
        assert compare("1.2.3", "1.2.3") == 0

    def test_gt(self):
        assert compare("2.0.0", "1.0.0") == 1

    def test_pre_lower_than_release(self):
        assert compare("1.0.0-rc.1", "1.0.0") == -1

    def test_pre_release_ordering(self):
        assert compare("1.0.0-rc.1", "1.0.0-rc.2") == -1

    def test_build_metadata_ignored(self):
        assert compare("1.2.3+build1", "1.2.3+build2") == 0


class TestIsValid:
    def test_valid(self):
        assert is_valid("1.0.0") is True
        assert is_valid("v0.1.0") is True
        assert is_valid("1.0.0-rc.1+build") is True

    def test_invalid(self):
        assert is_valid("1.0") is False
        assert is_valid("a.b.c") is False
        assert is_valid("") is False


class TestSortVersions:
    def test_ascending(self):
        result = sort_versions(["2.0.0", "1.2.3", "1.0.0", "1.2.0"])
        assert result == ["1.0.0", "1.2.0", "1.2.3", "2.0.0"]

    def test_with_pre_release(self):
        result = sort_versions(["1.0.0", "1.0.0-rc.2", "1.0.0-rc.1"])
        assert result == ["1.0.0-rc.1", "1.0.0-rc.2", "1.0.0"]


class TestNextPre:
    def test_from_release(self):
        assert next_pre("1.2.3") == "1.2.4-rc.1"

    def test_increments_existing_pre(self):
        assert next_pre("1.2.4-rc.1") == "1.2.4-rc.2"

    def test_custom_prefix(self):
        assert next_pre("1.2.3", prefix="beta") == "1.2.4-beta.1"


class TestSatisfies:
    def test_caret_major_nonzero(self):
        assert satisfies("1.5.0", "^1.2.3") is True
        assert satisfies("2.0.0", "^1.2.3") is False
        assert satisfies("1.2.2", "^1.2.3") is False

    def test_tilde(self):
        assert satisfies("1.2.5", "~1.2.3") is True
        assert satisfies("1.3.0", "~1.2.3") is False

    def test_and_range(self):
        assert satisfies("1.5.0", ">=1.0.0 <2.0.0") is True
        assert satisfies("2.0.0", ">=1.0.0 <2.0.0") is False

    def test_exact(self):
        assert satisfies("1.2.3", "=1.2.3") is True
        assert satisfies("1.2.4", "=1.2.3") is False


class TestExpandRange:
    def test_caret_major_nonzero(self):
        lower, upper = expand_range("^1.2.3")
        assert lower == Version(1, 2, 3)
        assert upper == Version(2, 0, 0)

    def test_caret_zero_major_nonzero_minor(self):
        lower, upper = expand_range("^0.2.3")
        assert lower == Version(0, 2, 3)
        assert upper == Version(0, 3, 0)

    def test_caret_zero_major_zero_minor(self):
        lower, upper = expand_range("^0.0.5")
        assert lower == Version(0, 0, 5)
        assert upper == Version(0, 0, 6)

    def test_tilde(self):
        lower, upper = expand_range("~1.2.3")
        assert lower == Version(1, 2, 3)
        assert upper == Version(1, 3, 0)

    def test_exact(self):
        lower, upper = expand_range("=1.2.3")
        assert lower == Version(1, 2, 3)
        assert upper == Version(1, 2, 4)

    def test_gte_unbounded(self):
        lower, upper = expand_range(">=1.0.0")
        assert lower == Version(1, 0, 0)
        assert upper is None

    def test_and_range(self):
        lower, upper = expand_range(">=1.0.0 <2.0.0")
        assert lower == Version(1, 0, 0)
        assert upper == Version(2, 0, 0)

    def test_lt_no_lower_bound_raises(self):
        with pytest.raises(ValueError):
            expand_range("<2.0.0")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            expand_range("")
