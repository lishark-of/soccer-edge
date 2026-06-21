from __future__ import annotations

import argparse
import json

from src.learning.history import build_learning_history


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="查看玩法权重学习和轻量调参建议。")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args(argv)
    history = build_learning_history()
    payload = {
        "status": "ok",
        "settled_count": history.get("settled_count", 0),
        "play_type_rows": history.get("play_type_rows", []),
        "category_rows": history.get("category_rows", []),
        "bucket_rows": history.get("bucket_rows", []),
        "combo_discipline_learning": history.get("combo_discipline_learning", {}),
        "strategy_adjustments": history.get("strategy_adjustments", []),
        "probability_quality": history.get("probability_quality", {}),
        "clv_history_summary": history.get("clv_history_summary", {}),
        "summary_zh": "玩法、赔率段、组合纪律和 CLV 学习只做轻量调权，不会自动绕过纪律门控。",
        "disclaimer": "学习权重审计只用于纸面研究和模型校准，不构成投注建议。",
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["summary_zh"])
        print(f"已结算样本：{payload['settled_count']}")
        for item in payload["strategy_adjustments"][:5]:
            print(f"- {item.get('label_zh')}: {item.get('reason_zh')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
