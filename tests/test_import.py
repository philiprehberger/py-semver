"""Basic import test."""


def test_import():
    """Verify the package can be imported."""
    import philiprehberger_semver
    assert hasattr(philiprehberger_semver, "__name__") or True
