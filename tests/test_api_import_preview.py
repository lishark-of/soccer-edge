from src.api.routes import dispatch_route


def test_api_import_preview_is_dry_run():
    response = dispatch_route(
        "/api/import/preview",
        {"input": "data/fixtures/import_sample_generic.csv", "adapter": "auto"},
    )
    assert response["ok"] is True
    assert response["data"]["dry_run"] is True
    assert response["data"]["output_path"] is None
