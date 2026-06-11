from __future__ import annotations

import re
import unicodedata

ALIASES = {
    "葡萄牙": "portugal",
    "葡萄牙队": "portugal",
    "尼日利亚": "nigeria",
    "英格兰": "england",
    "哥斯达": "costa rica",
    "哥斯达黎加": "costa rica",
    "鹿岛鹿角": "kashima antlers",
    "弗拉门戈": "flamengo",
    "浦项制铁": "pohang steelers",
    "博德闪耀": "bodo glimt",
    "罗森博格": "rosenborg",
    "马尔默": "malmo ff",
    "赫根": "hacken",
}

STOP_WORDS = {
    "fc", "cf", "sc", "club", "team", "national", "u23", "u21", "women",
    "football", "soccer", "the", "afc", "calcio", "ac", "as",
}


def canonical_team_name(value: str | None) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if text in ALIASES:
        return ALIASES[text]
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii") or text
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff ]+", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    if text in ALIASES:
        return ALIASES[text]
    parts = [part for part in text.split() if part not in STOP_WORDS]
    return " ".join(parts) if parts else text
