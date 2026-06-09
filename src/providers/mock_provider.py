from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.domain.match import Match
from src.domain.odds import MatchOdds, MarketOdds, OddsHistory, OddsHistoryPoint
from src.providers.base import BaseProvider


MOCK_MATCH_TEMPLATES = [
    ("001", "日职", "鹿岛鹿角", "横滨水手", True, "asia_evening", 62, 56, 0.03, 18),
    ("002", "韩K", "蔚山HD", "浦项制铁", True, "asia_evening", 60, 58, 0.05, 14),
    ("003", "挪超", "博德闪耀", "罗森博格", False, "europe_night", 67, 50, 0.02, 20),
    ("004", "瑞典超", "马尔默", "赫根", True, "europe_night", 64, 55, 0.04, 16),
    ("005", "巴甲", "弗拉门戈", "圣保罗", True, "americas_night", 61, 57, 0.07, 12),
]

MOCK_MARKET_BOOK = {
    "001": {
        "had": {"win": 1.82, "draw": 3.45, "lose": 4.20},
        "hhad": {"handicap": -1.0, "win": 3.55, "draw": 3.55, "lose": 1.84},
    },
    "002": {
        "had": {"win": 2.08, "draw": None, "lose": 3.38},
        "hhad": {"handicap": -1.0, "win": 4.10, "draw": None, "lose": 1.68},
    },
    "003": {
        "had": {"win": 1.71, "draw": 3.78, "lose": 4.65},
        "hhad": {"handicap": -1.0, "win": 3.10, "draw": 3.62, "lose": 2.02},
    },
    "004": {
        "had": {"win": 1.94, "draw": 3.52, "lose": 3.92},
        "hhad": {"handicap": -1.0, "win": 3.70, "draw": 3.48, "lose": 1.78},
    },
    "005": {
        "had": {"win": 2.22, "draw": 3.02, "lose": 3.15},
        "hhad": {"handicap": -1.0, "win": 4.40, "draw": 3.60, "lose": 1.62},
    },
}


def _tomorrow_date() -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    return (now + timedelta(days=1)).date().isoformat()


class MockProvider(BaseProvider):
    name = "mock"
    provider_name = "mock"

    def get_matches(self, date: str | None) -> list[Match]:
        target_date = date or _tomorrow_date()
        matches: list[Match] = []
        for index, item in enumerate(MOCK_MATCH_TEMPLATES, start=1):
            match_no, league, home, away, supports_single, group, home_rating, away_rating, draw_bias, sample_size = item
            kickoff_at = f"{target_date}T{12 + index * 2:02d}:00:00+08:00"
            market_book = MOCK_MARKET_BOOK[match_no]
            matches.append(
                Match(
                    match_id=f"{target_date.replace('-', '')}-{match_no}",
                    match_no=match_no,
                    date=target_date,
                    league=league,
                    kickoff_at=kickoff_at,
                    home_team=home,
                    away_team=away,
                    supports_single=supports_single,
                    correlation_group=group,
                    metadata={
                        "home_rating": home_rating,
                        "away_rating": away_rating,
                        "draw_bias": draw_bias,
                        "historical_sample_size": sample_size,
                        "league_uncertainty": 0.22 if "巴甲" in league else 0.12,
                    },
                    status="scheduled",
                    source="mock",
                    raw={"provider": "mock", "template_id": match_no},
                    had_odds=dict(market_book["had"]),
                    hhad_odds=dict(market_book["hhad"]),
                )
            )
        return matches

    def get_match_odds(self, match_id: str) -> MatchOdds:
        date_key = match_id.split("-")[0]
        match_no = match_id.split("-")[-1]
        target_date = f"{date_key[:4]}-{date_key[4:6]}-{date_key[6:8]}"
        matches = {match.match_id: match for match in self.get_matches(target_date)}
        match = matches[match_id]
        book = MOCK_MARKET_BOOK[match_no]
        updated_at = f"{match.date}T10:00:00+08:00"
        return MatchOdds(
            match_id=match.match_id,
            markets={
                "had": MarketOdds(
                    play_type="had",
                    outcomes={
                        "home": book["had"]["win"],
                        "draw": book["had"]["draw"],
                        "away": book["had"]["lose"],
                    },
                    source="mock",
                    last_updated=updated_at,
                ),
                "hhad": MarketOdds(
                    play_type="hhad",
                    handicap=book["hhad"]["handicap"],
                    outcomes={
                        "home": book["hhad"]["win"],
                        "draw": book["hhad"]["draw"],
                        "away": book["hhad"]["lose"],
                    },
                    source="mock",
                    last_updated=updated_at,
                ),
            },
        )

    def get_odds_history(self, match_id: str) -> OddsHistory:
        odds = self.get_match_odds(match_id)
        history: dict[str, list[OddsHistoryPoint]] = {}
        for market_key, market in odds.markets.items():
            values = [market.outcomes.get("home"), market.outcomes.get("draw"), market.outcomes.get("away")]
            if not all(isinstance(value, (int, float)) and value > 1 for value in values):
                continue
            home = float(market.outcomes["home"])
            draw = float(market.outcomes["draw"])
            away = float(market.outcomes["away"])
            history[market_key] = [
                OddsHistoryPoint(
                    snapshot_at=market.last_updated.replace("10:00:00", "08:00:00"),
                    outcomes={
                        "home": round(home * 1.03, 2),
                        "draw": round(draw * 0.99, 2),
                        "away": round(away * 0.97, 2),
                    },
                ),
                OddsHistoryPoint(
                    snapshot_at=market.last_updated.replace("10:00:00", "09:00:00"),
                    outcomes={
                        "home": round(home * 1.01, 2),
                        "draw": round(draw, 2),
                        "away": round(away * 0.99, 2),
                    },
                ),
                OddsHistoryPoint(
                    snapshot_at=market.last_updated,
                    outcomes=dict(market.outcomes),
                ),
            ]
        return OddsHistory(match_id=match_id, history=history)
