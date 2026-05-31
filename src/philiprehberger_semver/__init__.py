"""Parse, compare, bump, and validate semantic version strings."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

__all__ = [
    "Version",
    "parse",
    "bump",
    "compare",
    "satisfies",
    "is_valid",
    "sort_versions",
    "next_pre",
    "expand_range",
    "latest",
    "latest_stable",
]

_SEMVER_RE = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?$"
)


def _compare_pre_identifiers(a: list[str], b: list[str]) -> int:
    """Compare two lists of pre-release identifiers following semver 2.0 rules."""
    for id_a, id_b in zip(a, b):
        a_numeric = id_a.isdigit()
        b_numeric = id_b.isdigit()

        if a_numeric and b_numeric:
            diff = int(id_a) - int(id_b)
            if diff != 0:
                return -1 if diff < 0 else 1
        elif a_numeric:
            return -1
        elif b_numeric:
            return 1
        else:
            if id_a < id_b:
                return -1
            if id_a > id_b:
                return 1

    if len(a) < len(b):
        return -1
    if len(a) > len(b):
        return 1
    return 0


@dataclass
class Version:
    """Represents a semantic version following the semver 2.0.0 spec."""

    major: int
    minor: int
    patch: int
    pre: str = ""
    build: str = ""

    def _cmp(self, other: Version) -> int:
        # Compare major.minor.patch
        for a, b in [
            (self.major, other.major),
            (self.minor, other.minor),
            (self.patch, other.patch),
        ]:
            if a < b:
                return -1
            if a > b:
                return 1

        # Pre-release precedence
        if self.pre and other.pre:
            return _compare_pre_identifiers(
                self.pre.split("."), other.pre.split(".")
            )
        if self.pre:
            return -1
        if other.pre:
            return 1

        # Build metadata is ignored in comparison
        return 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._cmp(other) == 0

    def __lt__(self, other: Version) -> bool:
        return self._cmp(other) < 0

    def __le__(self, other: Version) -> bool:
        return self._cmp(other) <= 0

    def __gt__(self, other: Version) -> bool:
        return self._cmp(other) > 0

    def __ge__(self, other: Version) -> bool:
        return self._cmp(other) >= 0

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            s += f"-{self.pre}"
        if self.build:
            s += f"+{self.build}"
        return s

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.pre))


def parse(version: str) -> Version:
    """Parse a semver string into a ``Version`` object.

    Accepts an optional leading ``v`` prefix.  Raises ``ValueError`` if the
    string is not valid semver.
    """
    m = _SEMVER_RE.match(version)
    if m is None:
        raise ValueError(f"Invalid semver string: {version!r}")
    return Version(
        major=int(m.group("major")),
        minor=int(m.group("minor")),
        patch=int(m.group("patch")),
        pre=m.group("pre") or "",
        build=m.group("build") or "",
    )


def bump(version: str, part: str) -> str:
    """Bump *part* (``major``, ``minor``, or ``patch``) of a version string.

    Pre-release and build metadata are cleared after bumping.
    """
    v = parse(version)
    if part == "major":
        return str(Version(v.major + 1, 0, 0))
    if part == "minor":
        return str(Version(v.major, v.minor + 1, 0))
    if part == "patch":
        return str(Version(v.major, v.minor, v.patch + 1))
    raise ValueError(f"Invalid part: {part!r} (expected 'major', 'minor', or 'patch')")


def compare(a: str, b: str) -> int:
    """Compare two version strings.  Returns ``-1``, ``0``, or ``1``."""
    va = parse(a)
    vb = parse(b)
    return va._cmp(vb)


def is_valid(version: str) -> bool:
    """Return ``True`` if *version* is a valid semver string."""
    return _SEMVER_RE.match(version) is not None


def sort_versions(versions: list[str]) -> list[str]:
    """Sort a list of version strings in ascending semver order."""
    return [str(v) for v in sorted(parse(v) for v in versions)]


def next_pre(version: str, prefix: str = "rc") -> str:
    """Generate the next pre-release version.

    ``"1.2.3"`` becomes ``"1.2.4-rc.1"``.
    ``"1.2.4-rc.1"`` becomes ``"1.2.4-rc.2"``.
    """
    v = parse(version)

    if v.pre:
        parts = v.pre.split(".")
        if len(parts) >= 2 and parts[-1].isdigit():
            parts[-1] = str(int(parts[-1]) + 1)
            return str(Version(v.major, v.minor, v.patch, pre=".".join(parts)))
        return str(Version(v.major, v.minor, v.patch, pre=f"{v.pre}.1"))

    return str(Version(v.major, v.minor, v.patch + 1, pre=f"{prefix}.1"))


# ---------------------------------------------------------------------------
# satisfies() — range matching
# ---------------------------------------------------------------------------

_COMPARATOR_RE = re.compile(r"^(>=|<=|>|<|=)?(.+)$")


def _parse_comparator(token: str) -> tuple[str, Version]:
    """Parse a single comparator like ``>=1.0.0`` into (operator, Version)."""
    m = _COMPARATOR_RE.match(token)
    if m is None:
        raise ValueError(f"Invalid comparator: {token!r}")
    op = m.group(1) or "="
    return op, parse(m.group(2))


def _satisfies_single(v: Version, op: str, target: Version) -> bool:
    if op == ">=":
        return v >= target
    if op == "<=":
        return v <= target
    if op == ">":
        return v > target
    if op == "<":
        return v < target
    if op == "=":
        return v == target
    raise ValueError(f"Unknown operator: {op!r}")


def satisfies(version: str, range_str: str) -> bool:
    """Check whether *version* satisfies *range_str*.

    Supported range formats:

    * Simple comparators: ``>=1.0.0``, ``<2.0.0``
    * AND ranges (space-separated): ``>=1.0.0 <2.0.0``
    * Caret (``^1.2.3``): ``>=1.2.3 <2.0.0``
    * Tilde (``~1.2.3``): ``>=1.2.3 <1.3.0``
    """
    v = parse(version)
    range_str = range_str.strip()

    # Caret range: ^X.Y.Z -> >=X.Y.Z <(X+1).0.0
    if range_str.startswith("^"):
        target = parse(range_str[1:])
        if target.major != 0:
            upper = Version(target.major + 1, 0, 0)
        elif target.minor != 0:
            upper = Version(0, target.minor + 1, 0)
        else:
            upper = Version(0, 0, target.patch + 1)
        return v >= target and v < upper

    # Tilde range: ~X.Y.Z -> >=X.Y.Z <X.(Y+1).0
    if range_str.startswith("~"):
        target = parse(range_str[1:])
        upper = Version(target.major, target.minor + 1, 0)
        return v >= target and v < upper

    # Space-separated comparators (AND)
    tokens = range_str.split()
    for token in tokens:
        op, target = _parse_comparator(token)
        if not _satisfies_single(v, op, target):
            return False
    return True


def expand_range(range_str: str) -> tuple[Version, Version | None]:
    """Return the inclusive lower bound and exclusive upper bound of a range.

    The upper bound is ``None`` for ranges that are unbounded above (e.g.
    ``">=1.0.0"``).

    Args:
        range_str: A semver range expression in any format accepted by
            :func:`satisfies` — caret (``^1.2.3``), tilde (``~1.2.3``), an exact
            version, or space-separated comparators.

    Returns:
        Tuple of ``(lower_inclusive, upper_exclusive)``.

    Raises:
        ValueError: If the range cannot be parsed or has no lower bound.
    """
    range_str = range_str.strip()

    if range_str.startswith("^"):
        target = parse(range_str[1:])
        if target.major != 0:
            upper = Version(target.major + 1, 0, 0)
        elif target.minor != 0:
            upper = Version(0, target.minor + 1, 0)
        else:
            upper = Version(0, 0, target.patch + 1)
        return target, upper

    if range_str.startswith("~"):
        target = parse(range_str[1:])
        return target, Version(target.major, target.minor + 1, 0)

    tokens = range_str.split()
    if not tokens:
        raise ValueError("Empty range")

    # Single-token exact version
    if len(tokens) == 1:
        op, target = _parse_comparator(tokens[0])
        if op == "=":
            return target, Version(target.major, target.minor, target.patch + 1)
        if op == ">=":
            return target, None
        if op == ">":
            return Version(target.major, target.minor, target.patch + 1), None

    # Combine AND comparators
    lower: Version | None = None
    upper: Version | None = None

    for token in tokens:
        op, target = _parse_comparator(token)
        if op == ">=":
            if lower is None or target > lower:
                lower = target
        elif op == ">":
            candidate = Version(target.major, target.minor, target.patch + 1)
            if lower is None or candidate > lower:
                lower = candidate
        elif op == "<":
            if upper is None or target < upper:
                upper = target
        elif op == "<=":
            candidate = Version(target.major, target.minor, target.patch + 1)
            if upper is None or candidate < upper:
                upper = candidate
        elif op == "=":
            return target, Version(target.major, target.minor, target.patch + 1)
        else:
            raise ValueError(f"Unsupported operator in range: {op!r}")

    if lower is None:
        raise ValueError(f"Range has no lower bound: {range_str!r}")

    return lower, upper


def latest(versions: Iterable[str | Version]) -> Version | None:
    """Return the highest version, or ``None`` if the iterable is empty.

    String inputs are parsed via :func:`parse`.  Invalid version strings raise
    ``ValueError``.
    """
    parsed = [v if isinstance(v, Version) else parse(v) for v in versions]
    if not parsed:
        return None
    return max(parsed)


def latest_stable(versions: Iterable[str | Version]) -> Version | None:
    """Return the highest non-prerelease version, or ``None`` if none exist.

    Filters out prereleases (versions with a non-empty pre-release component)
    before picking the max.
    """
    parsed = [v if isinstance(v, Version) else parse(v) for v in versions]
    return latest(v for v in parsed if not v.pre)
