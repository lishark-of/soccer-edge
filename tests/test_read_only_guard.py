import pytest

from src.api.errors import ApiError
from src.api.read_only import ensure_read_only_operation
from src.api.routes import dispatch_route


def test_read_only_guard_rejects_write_operation():
    with pytest.raises(ApiError):
        ensure_read_only_operation("export", write_requested=True)


def test_api_read_only_rejects_export_param():
    with pytest.raises(ApiError):
        dispatch_route("/api/analyze", {"provider": "mock", "export": "xlsx"})
