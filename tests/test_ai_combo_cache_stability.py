import src.api.routes as routes
from src.api.routes import dispatch_route


def _success_payload():
    return {
        "provider_requested": "auto",
        "provider_target": "deepseek",
        "provider_resolved": "deepseek",
        "ds_status": "loaded",
        "ds_status_zh": "DS Pro 已参与",
        "ds_attempted": True,
        "ds_completed": True,
        "ds_error_code": "",
        "token_in": 120,
        "token_out": 80,
        "token_total": 200,
        "fallback_reason": "",
        "display_status_zh": "DS Pro 已参与本次研究。",
        "runtime_notice_zh": "本轮 DS 已成功返回，可直接查看 AI 研究摘要与 token 消耗。",
        "next_step_zh": "本轮已成功返回，可直接对照 AI 研究摘要、被拒原因和 token 消耗。",
        "ai_summary": {"warnings": []},
    }


def _failure_payload():
    return {
        "provider_requested": "auto",
        "provider_target": "deepseek",
        "provider_resolved": "deepseek",
        "ds_status": "error",
        "ds_status_zh": "DS 请求失败",
        "ds_attempted": True,
        "ds_completed": False,
        "ds_error_code": "network_error",
        "token_in": None,
        "token_out": None,
        "token_total": None,
        "fallback_reason": "DeepSeek 网络连接失败，已改用本地摘要。",
        "display_status_zh": "DeepSeek 网络连接失败，已改用本地摘要。",
        "runtime_notice_zh": "本轮 DS 已自动尝试，但未成功返回；当前原因：请求失败。",
        "next_step_zh": "已自动尝试；如仍回退，请查看最近一次异常并再次刷新今日观察。",
        "ai_summary": {"warnings": []},
    }


def test_ai_combo_route_does_not_cache_failed_fallback_payload(monkeypatch):
    routes._AI_COMBO_RESEARCH_CACHE.clear()
    calls = {"count": 0}

    def fake_build_ai_combo_research(result, run_ai=True, ai_provider="auto"):
        calls["count"] += 1
        if calls["count"] == 1:
            return _failure_payload()
        return _success_payload()

    monkeypatch.setattr(routes, "build_ai_combo_research", fake_build_ai_combo_research)
    first = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    second = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    assert first["ok"] is True
    assert second["ok"] is True
    assert calls["count"] == 2
    assert first["data"]["ds_completed"] is False
    assert second["data"]["ds_completed"] is True
    assert second["data"]["cache_status"] == "miss"
    status = dispatch_route("/api/llm/status", {})
    assert status["ok"] is True
    assert status["data"]["runtime_status"] == "loaded"
    assert status["data"]["token_total"] == 200


def test_ai_combo_route_reuses_persisted_ds_result_after_fresh_process_failure(monkeypatch, tmp_path):
    routes._AI_COMBO_RESEARCH_CACHE.clear()
    monkeypatch.setattr(routes.tempfile, "gettempdir", lambda: str(tmp_path))
    calls = {"count": 0}

    def fake_build_ai_combo_research(result, run_ai=True, ai_provider="auto"):
        calls["count"] += 1
        if calls["count"] == 1:
            return _success_payload()
        return _failure_payload()

    monkeypatch.setattr(routes, "build_ai_combo_research", fake_build_ai_combo_research)
    first = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    routes._AI_COMBO_RESEARCH_CACHE.clear()
    second = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10", "refresh": "1"})
    assert first["ok"] is True
    assert second["ok"] is True
    data = second["data"]
    assert calls["count"] == 2
    assert data["ds_completed"] is True
    assert data["reused_from_cached_ds"] is True
    assert data["cache_status"] == "stale_ds_hit"
    assert "本轮 DS 请求失败" in data["display_status_zh"]
    status = dispatch_route("/api/llm/status", {})
    assert status["ok"] is True
    assert status["data"]["runtime_status"] == "cached"
    assert status["data"]["token_total"] == 200
