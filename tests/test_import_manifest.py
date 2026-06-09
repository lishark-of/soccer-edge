from src.ingestion.manifest import build_import_manifest


def test_manifest_contains_sha256():
    manifest = build_import_manifest(
        "data/fixtures/import_sample_generic.csv",
        "generic_csv",
        10,
        10,
        0,
        None,
        [],
    )
    assert len(manifest["input_sha256"]) == 64
