from src.version import get_build_info, get_version


def test_version_string_present():
    assert get_version() == "0.1.0-local"
    assert get_build_info()["release_phase"] == "phase2i"
