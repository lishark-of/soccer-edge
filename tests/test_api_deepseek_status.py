import src.api.routes as routes
import src.explain.ai_combo_research as ai_combo
from src.api.routes import dispatch_route
from src.explain.deepseek_runtime import reset_runtime_status, update_runtime_status


def test_api_llm_status_hides_api_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-value")
    payload = dispatch_route("/api/llm/status", {})
    assert payload["ok"] is True
    assert payload["data"]["api_key_present"] is True
    assert "ds_attempted" in payload["data"]
    assert "ds_completed" in payload["data"]
    assert "ds_error_code" in payload["data"]
    assert "decision_chain" in payload["data"]
    assert "ready_for_auto" in payload["data"]
    assert "secret-value" not in str(payload)


def test_api_llm_status_exposes_runtime_fallback_reason_and_status_object(monkeypatch):
    reset_runtime_status()
    monkeypatch.setenv("JC_EDGE_DEEPSEEK_ENABLED", "true")
    monkeypatch.setenv("JC_EDGE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-value")
    update_runtime_status(
        provider_requested="auto",
        provider_target="deepseek",
        provider_resolved="local",
        ds_status="error",
        ds_status_zh="DS 请求失败",
        ds_attempted=True,
        ds_completed=False,
        ds_error_code="invalid_api_key",
        fallback_reason="DeepSeek Key 无效，已改用本地摘要。",
        token_in=None,
        token_out=None,
        token_total=None,
    )
    payload = dispatch_route("/api/llm/status", {})
    assert payload["ok"] is True
    data = payload["data"]
    assert data["fallback_reason"] == "DeepSeek Key 无效，已改用本地摘要。"
    assert data["ai_research_status"]["status"] == "fallback"
    assert data["ai_research_status"]["label_zh"] == "Key 无效"
    assert data["ai_research_status"]["summary_zh"] == "DeepSeek Key 无效，已改用本地摘要。"


def test_learning_history_view_returns_daily_and_window_metrics():
    payload = dispatch_route("/api/view/learning-history", {})
    assert payload["ok"] is True
    data = payload["data"]
    assert "daily_metrics" in data
    assert "window_metrics" in data
    assert "daily_digest" in data
    assert "window_digests" in data


def test_view_optimizer_runs_ai_by_default(monkeypatch):
    monkeypatch.delenv("JC_EDGE_DEEPSEEK_ENABLED", raising=False)
    monkeypatch.delenv("FOOTBALL_JC_LLM_ENABLED", raising=False)
    payload = dispatch_route("/api/view/optimizer", {"provider": "mock", "date": "2026-06-10"})
    assert payload["ok"] is True
    ai = payload["data"]["ai_combo_research"]
    assert "ds_status" in ai
    assert "ds_status_zh" in ai
    assert "fallback_reason" in ai
    assert "token_total" in ai
    assert "config_status_zh" in ai
    assert "runtime_notice_zh" in ai
    assert "next_step_zh" in ai
    assert "ai_research_layer" in payload["data"]
    assert "daily_learning_digest" in payload["data"]
    assert "window_learning_digests" in payload["data"]


def test_ai_combo_route_runs_by_default(monkeypatch):
    monkeypatch.delenv("JC_EDGE_DEEPSEEK_ENABLED", raising=False)
    monkeypatch.delenv("FOOTBALL_JC_LLM_ENABLED", raising=False)
    payload = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    assert payload["ok"] is True
    data = payload["data"]
    assert "provider_requested" in data
    assert "provider_resolved" in data
    assert "display_status_zh" in data
    assert "config_status_zh" in data
    assert "runtime_notice_zh" in data
    assert "next_step_zh" in data


def test_optimizer_pre_match_includes_ai_research_by_default(monkeypatch):
    monkeypatch.delenv("JC_EDGE_DEEPSEEK_ENABLED", raising=False)
    monkeypatch.delenv("FOOTBALL_JC_LLM_ENABLED", raising=False)
    payload = dispatch_route("/api/optimizer/pre-match", {"provider": "mock", "date": "2026-06-10"})
    assert payload["ok"] is True
    ai = payload["data"]["ai_combo_research"]
    assert "ds_status" in ai
    assert "provider_target" in ai
    assert "provider_resolved" in ai
    assert "display_status_zh" in ai
    assert "llm_status" in payload["data"]
    assert "ai_research_status" in payload["data"]


def test_ai_combo_route_includes_gate_context(monkeypatch):
    monkeypatch.delenv("JC_EDGE_DEEPSEEK_ENABLED", raising=False)
    monkeypatch.delenv("FOOTBALL_JC_LLM_ENABLED", raising=False)
    payload = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    assert payload["ok"] is True
    data = payload["data"]
    assert "credibility_gate" in data
    assert "no_combo_reason" in data
    assert "best_risk_adjusted_final_status" in data
    assert "daily_learning_metrics" in data
    assert "window_learning_metrics" in data
    assert "daily_learning_digest" in data
    assert "window_learning_digests" in data


def test_ai_combo_route_reuses_short_cache(monkeypatch):
    calls = {"count": 0}
    routes._AI_COMBO_RESEARCH_CACHE.clear()

    def fake_build_ai_combo_research(result, run_ai=True, ai_provider="auto"):
        calls["count"] += 1
        return {
            "provider_target": "deepseek",
            "provider_resolved": "deepseek",
            "ds_status": "loaded",
            "ds_attempted": True,
            "ds_completed": True,
            "ds_error_code": "",
            "token_in": 100,
            "token_out": 50,
            "token_total": 150,
            "fallback_reason": "",
            "display_status_zh": "DS Pro 已参与本次研究。",
            "ai_summary": {"warnings": []},
        }

    monkeypatch.setattr(routes, "build_ai_combo_research", fake_build_ai_combo_research)
    first = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    second = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    assert first["ok"] is True
    assert second["ok"] is True
    assert calls["count"] == 1
    assert first["data"]["cache_status"] == "miss"
    assert second["data"]["cache_status"] == "hit"


def test_ai_combo_route_retries_empty_content_before_fallback(monkeypatch):
    calls = {"count": 0}
    routes._AI_COMBO_RESEARCH_CACHE.clear()

    def fake_status():
        return {
            "status": "ready",
            "fallback_reason": "",
            "ready_for_auto": True,
            "max_input_tokens": 24000,
            "max_output_tokens": 4000,
        }

    def fake_explain(kind, payload, context):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "provider": "local",
                "status": "error",
                "status_zh": "DS 请求失败",
                "text": "本地摘要",
                "warnings": ["first failed"],
                "provider_requested": "deepseek",
                "provider_resolved": "local",
                "ds_status": "error",
                "ds_status_zh": "DS 请求失败",
                "ds_attempted": True,
                "ds_completed": False,
                "ds_error_code": "empty_content",
                "token_in": None,
                "token_out": None,
                "token_total": None,
                "fallback_reason": "DeepSeek 未返回有效解释内容，已改用本地摘要。",
                "display_status_zh": "DeepSeek 未返回有效解释内容，已改用本地摘要。",
            }
        return {
            "provider": "deepseek",
            "status": "loaded",
            "status_zh": "DS Pro 已参与",
            "text": "DS 成功摘要",
            "warnings": [],
            "provider_requested": "deepseek",
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
        }

    monkeypatch.setattr(ai_combo, "llm_status_payload", fake_status)
    monkeypatch.setattr(ai_combo, "explain_with_optional_deepseek", fake_explain)
    payload = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    assert payload["ok"] is True
    data = payload["data"]
    assert calls["count"] >= 2
    assert data["ds_completed"] is True
    assert data["ds_error_code"] == ""
    assert data["token_total"] == 200
    assert data["ai_research_status"]["status"] == "done"
    assert data["ai_research_status"]["label_zh"] == "DS Pro 已参与"
    assert data["display_status_zh"] == "首次请求未返回可用正文后已自动重试并成功返回。"


def test_ai_combo_route_refreshes_runtime_guidance_after_current_success(monkeypatch):
    reset_runtime_status()
    routes._AI_COMBO_RESEARCH_CACHE.clear()
    calls = {"status": 0}

    def fake_status():
        calls["status"] += 1
        if calls["status"] >= 4:
            return {
                "status": "ready",
                "fallback_reason": "",
                "ready_for_auto": True,
                "max_input_tokens": 24000,
                "max_output_tokens": 4000,
                "config_status_zh": "DeepSeek 已就绪，当前模型 deepseek-v4-pro。",
                "runtime_notice_zh": "本轮 DS 已成功返回，可直接查看 AI 研究摘要与 token 消耗。",
                "next_step_zh": "本轮已成功返回，可直接对照 AI 研究摘要、被拒原因和 token 消耗。",
            }
        return {
            "status": "ready",
            "fallback_reason": "",
            "ready_for_auto": True,
            "max_input_tokens": 24000,
            "max_output_tokens": 4000,
            "config_status_zh": "DeepSeek 已就绪，当前模型 deepseek-v4-pro。",
            "runtime_notice_zh": "本轮还没有自动研究记录。",
            "next_step_zh": "刷新今日观察或赛前优化后，会自动触发 DS 研究。",
        }

    def fake_explain(kind, payload, context):
        return {
            "provider": "deepseek",
            "status": "loaded",
            "status_zh": "DS Pro 已参与",
            "text": "DS 成功摘要",
            "warnings": [],
            "provider_requested": "deepseek",
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
        }

    monkeypatch.setattr(routes, "llm_status_payload", fake_status)
    monkeypatch.setattr(ai_combo, "llm_status_payload", fake_status)
    monkeypatch.setattr(ai_combo, "explain_with_optional_deepseek", fake_explain)
    payload = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10", "refresh": "1"})
    assert payload["ok"] is True
    data = payload["data"]
    assert data["ds_completed"] is True
    assert data["runtime_notice_zh"] == "本轮 DS 已成功返回，可直接查看 AI 研究摘要与 token 消耗。"
    assert data["next_step_zh"] == "本轮已成功返回，可直接对照 AI 研究摘要、被拒原因和 token 消耗。"


def test_ai_combo_route_reuses_last_successful_ds_result_when_refresh_fails(monkeypatch):
    routes._AI_COMBO_RESEARCH_CACHE.clear()
    calls = {"count": 0}

    def fake_build_ai_combo_research(result, run_ai=True, ai_provider="auto"):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "provider_requested": "auto",
                "provider_target": "deepseek",
                "provider_resolved": "deepseek",
                "ds_status": "loaded",
                "ds_status_zh": "DS Pro 已参与",
                "ds_attempted": True,
                "ds_completed": True,
                "ds_error_code": "",
                "token_in": 100,
                "token_out": 50,
                "token_total": 150,
                "fallback_reason": "",
                "display_status_zh": "DS Pro 已参与本次研究。",
                "runtime_notice_zh": "本轮 DS 已成功返回，可直接查看 AI 研究摘要与 token 消耗。",
                "next_step_zh": "本轮已成功返回，可直接对照 AI 研究摘要、被拒原因和 token 消耗。",
                "ai_summary": {"warnings": []},
            }
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

    monkeypatch.setattr(routes, "build_ai_combo_research", fake_build_ai_combo_research)
    first = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10"})
    second = dispatch_route("/api/view/ai-combo-research", {"provider": "mock", "date": "2026-06-10", "refresh": "1"})
    assert first["ok"] is True
    assert second["ok"] is True
    data = second["data"]
    assert calls["count"] == 2
    assert data["cache_status"] == "stale_ds_hit"
    assert data["reused_from_cached_ds"] is True
    assert data["ds_status"] == "cached"
    assert data["ds_completed"] is True
    assert data["token_total"] == 150
    assert data["display_status_zh"] == "本轮 DS 请求失败，已复用最近一次 DS 研究结果。"
    assert data["fallback_reason"] == "DeepSeek 网络连接失败，已改用本地摘要。"
    assert data["live_attempt"]["ds_error_code"] == "network_error"
    status = dispatch_route("/api/llm/status", {})
    assert status["ok"] is True
    assert status["data"]["runtime_status"] == "cached"
    assert status["data"]["runtime_notice_zh"] == "本轮 DS 请求失败，已复用最近一次成功的 DS 研究结果。"
    assert status["data"]["next_step_zh"] == "当前可先查看缓存研究；如需最新解释，可稍后刷新，若持续失败请检查 Key、额度或网络。"


def test_optimizer_pre_match_reuses_last_successful_ds_result_when_refresh_fails(monkeypatch):
    routes._AI_COMBO_RESEARCH_CACHE.clear()
    calls = {"count": 0}

    def fake_build_ai_combo_research(result, run_ai=True, ai_provider="auto"):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "provider_requested": "auto",
                "provider_target": "deepseek",
                "provider_resolved": "deepseek",
                "ds_status": "loaded",
                "ds_status_zh": "DS Pro 已参与",
                "ds_attempted": True,
                "ds_completed": True,
                "ds_error_code": "",
                "token_in": 90,
                "token_out": 45,
                "token_total": 135,
                "fallback_reason": "",
                "display_status_zh": "DS Pro 已参与本次研究。",
                "runtime_notice_zh": "本轮 DS 已成功返回，可直接查看 AI 研究摘要与 token 消耗。",
                "next_step_zh": "本轮已成功返回，可直接对照 AI 研究摘要、被拒原因和 token 消耗。",
                "ai_summary": {"warnings": []},
            }
        return {
            "provider_requested": "auto",
            "provider_target": "deepseek",
            "provider_resolved": "deepseek",
            "ds_status": "error",
            "ds_status_zh": "DS 请求失败",
            "ds_attempted": True,
            "ds_completed": False,
            "ds_error_code": "request_timeout",
            "token_in": None,
            "token_out": None,
            "token_total": None,
            "fallback_reason": "DeepSeek 请求超时，已改用本地摘要。",
            "display_status_zh": "DeepSeek 请求超时，已改用本地摘要。",
            "runtime_notice_zh": "本轮 DS 已自动尝试，但未成功返回；当前原因：请求超时。",
            "next_step_zh": "已自动尝试；如仍回退，请查看最近一次异常并再次刷新今日观察。",
            "ai_summary": {"warnings": []},
        }

    monkeypatch.setattr(routes, "build_ai_combo_research", fake_build_ai_combo_research)
    first = dispatch_route("/api/optimizer/pre-match", {"provider": "mock", "date": "2026-06-10"})
    second = dispatch_route("/api/optimizer/pre-match", {"provider": "mock", "date": "2026-06-10", "refresh": "1"})
    assert first["ok"] is True
    assert second["ok"] is True
    data = second["data"]["ai_combo_research"]
    assert calls["count"] == 2
    assert data["cache_status"] == "stale_ds_hit"
    assert data["reused_from_cached_ds"] is True
    assert data["ds_status"] == "cached"
    assert data["ds_completed"] is True
    assert data["token_total"] == 135
    assert data["display_status_zh"] == "本轮 DS 请求失败，已复用最近一次 DS 研究结果。"
    assert data["fallback_reason"] == "DeepSeek 请求超时，已改用本地摘要。"
    assert data["live_attempt"]["ds_error_code"] == "request_timeout"
