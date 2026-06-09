from __future__ import annotations


def build_quality_report(matches: list, skipped_rows: list | None = None) -> dict:
    skipped_rows = skipped_rows or []
    dates = sorted(match.date for match in matches)
    leagues = {match.league for match in matches if match.league}
    teams = {team for match in matches for team in (match.home_team, match.away_team) if team}
    result_counts = {"H": 0, "D": 0, "A": 0}
    had_count = 0
    hhad_count = 0
    for match in matches:
        result_counts[match.result_1x2] = result_counts.get(match.result_1x2, 0) + 1
        if match.odds_had:
            had_count += 1
        if match.odds_hhad:
            hhad_count += 1
    total = len(matches)
    warnings = []
    if total < 20:
        warnings.append("sample size is low")
    if total and had_count / total < 0.5:
        warnings.append("HAD odds coverage is below 50%")
    if len(teams) < 4 and total:
        warnings.append("team coverage is narrow")
    if skipped_rows:
        warnings.append(f"{len(skipped_rows)} rows skipped during normalization")
    return {
        "matches": total,
        "date_min": dates[0] if dates else None,
        "date_max": dates[-1] if dates else None,
        "leagues": len(leagues),
        "teams": len(teams),
        "odds_coverage": {
            "had": round(had_count / total, 6) if total else 0.0,
            "hhad": round(hhad_count / total, 6) if total else 0.0,
        },
        "result_distribution": result_counts,
        "skipped_rows": len(skipped_rows),
        "warnings": warnings,
    }
