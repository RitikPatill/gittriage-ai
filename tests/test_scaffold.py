def test_package_importable():
    import gittriage  # noqa: F401


def test_cli_app_exists():
    from gittriage.cli import app
    assert app is not None
