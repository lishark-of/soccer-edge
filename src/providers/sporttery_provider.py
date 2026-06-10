from __future__ import annotations

import json
import ssl
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.domain.match import Match
from src.domain.odds import MatchOdds, MarketOdds, OddsHistory, OddsHistoryPoint
from src.providers.base import BaseProvider, ProviderError


class SportteryProvider(BaseProvider):
    name = "sporttery"
    provider_name = "sporttery"
    base_url = "https://webapi.sporttery.cn/gateway"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.sporttery.cn/",
        "Origin": "https://www.sporttery.cn",
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self._match_cache: dict[str, Match] = {}
        self._odds_cache: dict[str, MatchOdds] = {}

    def get_matches(self, date: str | None = None) -> list[Match]:
        target_date = date
        selling_matches = self._get_selling_matches()
        if target_date:
            filtered = [
                match
                for match in selling_matches
                if match.date == target_date or str((match.raw or {}).get("businessDate") or "") == target_date
            ]
            if filtered:
                return filtered
            return self._get_results_by_date(target_date)
        if selling_matches:
            return selling_matches
        return self._get_recent_results()

    def get_match_odds(self, match_id: str) -> MatchOdds:
        if match_id in self._odds_cache:
            return self._odds_cache[match_id]
        self.get_matches(None)
        if match_id not in self._odds_cache:
            raise ProviderError(f"odds unavailable for match_id={match_id}")
        return self._odds_cache[match_id]

    def get_odds_history(self, match_id: str) -> OddsHistory:
        try:
            value = self._request_value(
                "/uniform/football/getFixedBonusV1.qry",
                {"clientCode": "3001", "matchId": match_id},
            )
        except ProviderError:
            return OddsHistory(match_id=match_id, history={})
        history = {
            "had": self._parse_history_points(value.get("oddsHistory", {}).get("hadList", [])),
            "hhad": self._parse_history_points(value.get("oddsHistory", {}).get("hhadList", [])),
        }
        history = {key: value for key, value in history.items() if value}
        return OddsHistory(match_id=match_id, history=history)

    def _get_selling_matches(self) -> list[Match]:
        value = self._request_value("/uniform/football/getMatchListV1.qry", {"clientCode": "3001"})
        matches: list[Match] = []
        for group in value.get("matchInfoList", []):
            for raw_match in group.get("subMatchList", []):
                if isinstance(raw_match, dict):
                    parsed = self._parse_selling_match(raw_match)
                    if parsed is not None:
                        matches.append(parsed)
        return matches

    def _get_recent_results(self) -> list[Match]:
        today = datetime.now()
        return self._query_results(
            (today - timedelta(days=14)).strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d"),
        )

    def _get_results_by_date(self, date: str) -> list[Match]:
        return self._query_results(date, date)

    def _query_results(self, start_date: str, end_date: str) -> list[Match]:
        value = self._request_value(
            "/uniform/football/getUniformMatchResultV1.qry",
            {
                "matchBeginDate": start_date,
                "matchEndDate": end_date,
                "leagueId": "",
                "pageSize": "60",
                "pageNo": "1",
                "isFix": "0",
                "matchPage": "1",
                "pcOrWap": "1",
            },
        )
        matches: list[Match] = []
        for raw_match in value.get("matchResult", []):
            if isinstance(raw_match, dict):
                parsed = self._parse_result_match(raw_match)
                if parsed is not None:
                    matches.append(parsed)
        return matches

    def _request_value(self, endpoint: str, params: dict[str, object]) -> dict[str, object]:
        query = urlencode(params)
        request = Request(
            f"{self.base_url}{endpoint}?{query}",
            headers=self.headers,
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
            payload = json.loads(raw)
        except Exception as exc:
            if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
                raise ProviderError(self._short_error(exc)) from exc
            try:
                with urlopen(request, timeout=self.timeout, context=ssl._create_unverified_context()) as response:
                    raw = response.read().decode("utf-8")
                payload = json.loads(raw)
                warnings = getattr(self, "warnings", None)
                if warnings is None:
                    warnings = []
                    setattr(self, "warnings", warnings)
                warning = "sporttery ssl fallback used for official webapi host"
                if warning not in warnings:
                    warnings.append(warning)
            except Exception as fallback_exc:
                raise ProviderError(self._short_error(fallback_exc)) from fallback_exc
        if payload.get("success") is False:
            raise ProviderError(str(payload.get("errorMessage") or "sporttery request failed"))
        value = payload.get("value")
        if not isinstance(value, dict):
            raise ProviderError("sporttery response missing value payload")
        return value

    def _parse_selling_match(self, raw_match: dict[str, object]) -> Match | None:
        match_id = str(raw_match.get("matchId") or "").strip()
        if not match_id:
            return None
        match_date = str(raw_match.get("matchDate") or "").strip()
        kickoff_time = str(raw_match.get("matchTime") or "00:00").strip()
        kickoff_at = f"{match_date}T{kickoff_time}:00+08:00"
        had_preview, had_market = self._extract_pool(raw_match.get("oddsList") or [], "HAD")
        hhad_preview, hhad_market = self._extract_pool(raw_match.get("oddsList") or [], "HHAD")
        home_rating, away_rating, draw_bias = self._ratings_from_had(had_preview or {})
        match = Match(
            match_id=match_id,
            match_no=str(raw_match.get("matchNumStr") or ""),
            date=match_date,
            league=str(raw_match.get("leagueAbbName") or raw_match.get("leagueName") or ""),
            kickoff_at=kickoff_at,
            home_team=str(raw_match.get("homeTeamAbbName") or raw_match.get("homeTeam") or ""),
            away_team=str(raw_match.get("awayTeamAbbName") or raw_match.get("awayTeam") or ""),
            supports_single=bool(raw_match.get("sellSingle") or raw_match.get("single") or False),
            correlation_group=match_date,
            metadata={
                "home_rating": home_rating,
                "away_rating": away_rating,
                "draw_bias": draw_bias,
                "historical_sample_size": 16,
                "league_uncertainty": 0.16,
            },
            status=str(raw_match.get("matchStatus") or "scheduled"),
            source="sporttery",
            raw=dict(raw_match),
            had_odds=had_preview,
            hhad_odds=hhad_preview,
        )
        markets: dict[str, MarketOdds] = {}
        if had_market is not None:
            markets["had"] = had_market
        if hhad_market is not None:
            markets["hhad"] = hhad_market
        self._match_cache[match.match_id] = match
        self._odds_cache[match.match_id] = MatchOdds(match_id=match.match_id, markets=markets)
        return match

    def _parse_result_match(self, raw_match: dict[str, object]) -> Match | None:
        match_id = str(raw_match.get("matchId") or "").strip()
        if not match_id:
            return None
        match_date = str(raw_match.get("matchDate") or "").strip()
        full_score = str(raw_match.get("sectionsNo999") or "").strip()
        home_goals, away_goals = self._score_pair(full_score)
        had_preview = {
            "win": self._safe_float(raw_match.get("h")),
            "draw": self._safe_float(raw_match.get("d")),
            "lose": self._safe_float(raw_match.get("a")),
        }
        had_market = None
        had_outcomes = {
            "home": had_preview["win"],
            "draw": had_preview["draw"],
            "away": had_preview["lose"],
        }
        if self._has_usable_outcomes(had_outcomes):
            had_market = MarketOdds(
                play_type="had",
                outcomes=had_outcomes,
                source="sporttery",
                last_updated=f"{match_date}T12:00:00+08:00",
            )
        match = Match(
            match_id=match_id,
            match_no=str(raw_match.get("matchNumStr") or ""),
            date=match_date,
            league=str(raw_match.get("leagueNameAbbr") or raw_match.get("leagueAbbName") or ""),
            kickoff_at=f"{match_date}T20:00:00+08:00",
            home_team=str(raw_match.get("homeTeam") or raw_match.get("homeTeamAbbName") or ""),
            away_team=str(raw_match.get("awayTeam") or raw_match.get("awayTeamAbbName") or ""),
            supports_single=False,
            correlation_group=match_date,
            metadata={
                "home_rating": 56,
                "away_rating": 56,
                "draw_bias": 0.04,
                "historical_sample_size": 12,
                "league_uncertainty": 0.18,
                "full_score": full_score,
                "home_goals": home_goals,
                "away_goals": away_goals,
            },
            status="finished",
            source="sporttery",
            raw=dict(raw_match),
            had_odds=had_preview,
            hhad_odds=None,
        )
        self._match_cache[match.match_id] = match
        self._odds_cache[match.match_id] = MatchOdds(
            match_id=match.match_id,
            markets={"had": had_market} if had_market is not None else {},
        )
        return match

    def _extract_pool(
        self,
        odds_list: list[object],
        pool_code: str,
    ) -> tuple[dict[str, float | None] | None, MarketOdds | None]:
        for item in odds_list:
            if not isinstance(item, dict) or str(item.get("poolCode") or "") != pool_code:
                continue
            preview = {
                "win": self._safe_float(item.get("h")),
                "draw": self._safe_float(item.get("d")),
                "lose": self._safe_float(item.get("a")),
            }
            if pool_code == "HHAD":
                preview = {"handicap": self._safe_float(item.get("goalLine")), **preview}
            outcomes = {
                "home": preview.get("win"),
                "draw": preview.get("draw"),
                "away": preview.get("lose"),
            }
            market = None
            handicap = preview.get("handicap") if pool_code == "HHAD" else None
            if self._has_usable_outcomes(outcomes) and (pool_code != "HHAD" or handicap is not None):
                market = MarketOdds(
                    play_type="hhad" if pool_code == "HHAD" else "had",
                    outcomes=outcomes,
                    handicap=handicap,
                    source="sporttery",
                    last_updated=self._last_updated(item),
                )
            return preview, market
        return None, None

    def _parse_history_points(self, raw_items: list[object]) -> list[OddsHistoryPoint]:
        points: list[OddsHistoryPoint] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            outcomes = {
                "home": self._safe_float(item.get("h")),
                "draw": self._safe_float(item.get("d")),
                "away": self._safe_float(item.get("a")),
            }
            if not self._has_usable_outcomes(outcomes):
                continue
            date_part = str(item.get("updateDate") or "").strip()
            time_part = str(item.get("updateTime") or "00:00").strip()
            points.append(
                OddsHistoryPoint(
                    snapshot_at=f"{date_part}T{time_part}:00+08:00",
                    outcomes=outcomes,
                )
            )
        return points

    def _ratings_from_had(self, preview: dict[str, float | None]) -> tuple[int, int, float]:
        home = preview.get("win") or 2.4
        away = preview.get("lose") or 2.4
        gap = max(-14, min(14, round((away - home) * 6)))
        home_rating = 56 + gap
        away_rating = 56 - gap
        draw_bias = 0.03 if abs(gap) >= 4 else 0.05
        return home_rating, away_rating, draw_bias

    @staticmethod
    def _score_pair(score: str) -> tuple[int | None, int | None]:
        if ":" not in score:
            return None, None
        left, right = score.split(":", 1)
        try:
            return int(left), int(right)
        except ValueError:
            return None, None

    @staticmethod
    def _has_usable_outcomes(outcomes: dict[str, float | None]) -> bool:
        values = [outcomes.get("home"), outcomes.get("draw"), outcomes.get("away")]
        return all(isinstance(value, (int, float)) and value > 1 for value in values)

    @staticmethod
    def _safe_float(value: object) -> float | None:
        if value in (None, ""):
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _last_updated(item: dict[str, object]) -> str:
        date_part = str(item.get("updateDate") or "").strip()
        time_part = str(item.get("updateTime") or "00:00").strip()
        if date_part:
            return f"{date_part}T{time_part}:00+08:00"
        return ""

    @staticmethod
    def _short_error(exc: Exception) -> str:
        text = str(exc).strip().replace("\n", " ")
        return text[:180] or exc.__class__.__name__
