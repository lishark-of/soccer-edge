from src.cli import launch_app


def test_launch_app_cli_help_or_importable():
    assert callable(launch_app.main)
    assert launch_app.LOCAL_HOSTS == {"127.0.0.1", "localhost"}
