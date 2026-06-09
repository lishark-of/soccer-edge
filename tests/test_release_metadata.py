from src.api.routes import dispatch_route
from src.release.metadata import build_release_metadata


def test_release_metadata_contains_disabled_capabilities():
    metadata = build_release_metadata()
    assert "betting" in metadata["disabled_capabilities"]
    assert metadata["version"] == "0.1.0-local"


def test_api_info_contains_version():
    payload = dispatch_route("/api/info", {})
    assert payload["data"]["version"] == "0.1.0-local"
    assert payload["data"]["release_phase"] == "phase2i"
