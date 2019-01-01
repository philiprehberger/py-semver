# philiprehberger-semver

Parse, compare, bump, and validate semantic version strings.

## Install

```bash
pip install philiprehberger-semver
```

## Usage

```python
from philiprehberger_semver import parse, bump, compare, satisfies, is_valid, sort_versions, next_pre
```

### Parsing

```python
v = parse("1.2.3-beta.1+build.42")
v.major  # 1
v.minor  # 2
v.patch  # 3
v.pre    # "beta.1"
v.build  # "build.42"
str(v)   # "1.2.3-beta.1+build.42"
```

A leading `v` prefix is accepted:

```python
parse("v2.0.0")  # Version(major=2, minor=0, patch=0)
```

### Bumping

```python
bump("1.2.3", "major")  # "2.0.0"
bump("1.2.3", "minor")  # "1.3.0"
bump("1.2.3", "patch")  # "1.2.4"
```

### Comparing

```python
compare("1.2.3", "1.3.0")  # -1
compare("2.0.0", "2.0.0")  #  0
compare("3.0.0", "2.9.9")  #  1
```

### Range matching

```python
satisfies("1.5.0", ">=1.0.0 <2.0.0")  # True
satisfies("1.2.5", "^1.2.3")           # True  (>=1.2.3 <2.0.0)
satisfies("1.2.5", "~1.2.3")           # True  (>=1.2.3 <1.3.0)
satisfies("1.3.0", "~1.2.3")           # False
```

### Validation

```python
is_valid("1.2.3")        # True
is_valid("not-a-version") # False
```

### Sorting

```python
sort_versions(["2.0.0", "1.0.0", "1.1.0"])  # ["1.0.0", "1.1.0", "2.0.0"]
```

### Pre-release generation

```python
next_pre("1.2.3")         # "1.2.4-rc.1"
next_pre("1.2.4-rc.1")    # "1.2.4-rc.2"
next_pre("1.2.3", "beta") # "1.2.4-beta.1"
```

## API

| Function | Description |
|----------|-------------|
| `parse(version)` | Parse a semver string into a `Version` object |
| `bump(version, part)` | Bump major, minor, or patch and return the new version string |
| `compare(a, b)` | Compare two version strings, returns -1, 0, or 1 |
| `satisfies(version, range_str)` | Check if a version satisfies a range (`>=`, `<`, `^`, `~`) |
| `is_valid(version)` | Check if a string is valid semver |
| `sort_versions(versions)` | Sort a list of version strings in ascending order |
| `next_pre(version, prefix)` | Generate the next pre-release version string |

## License

MIT
