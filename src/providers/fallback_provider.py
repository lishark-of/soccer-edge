from __future__ import annotations

from src.domain.odds import OddsHistory
from src.providers.base import BaseProvider, ProviderError
from src.providers.mock_provider import MockProvider
from src.providers.sporttery_provider import SportteryProvider


class FallbackProvider(BaseProvider):
    name = "auto"
    provider_name = "auto"

    def __init__(
        self,
        primary: BaseProvider | None = None,
        fallback: BaseProvider | None = None,
        allow_empty_primary: bool = False,
    ):
        self.primary = primary or SportteryProvider()
        self.fallback = fallback or MockProvider()
        self.allow_empty_primary = allow_empty_primary
        self.provider_used = getattr(self.primary, "provider_name", "sporttery")
        self.resolved_provider_name = self.provider_used
        self.fallback_used = False
        self.warnings: list[str] = []
        self.messages = self.warnings
        self._active_provider: BaseProvider = self.primary

    def get_matches(self, date: str | None = None):
        self.warnings.clear()
        self.fallback_used = False
        try:
            matches = self.primary.get_matches(date)
            if matches is None:
                raise ProviderError("returned no matches")
            if not matches and not self.allow_empty_primary:
                raise ProviderError("returned no matches")
            self._activate(self.primary)
            return matches
        except Exception as exc:
            warning = self._format_fallback_warning(exc)
            self.warnings.append(warning)
            self.fallback_used = True
            self._activate(self.fallback)
            return self.fallback.get_matches(date)

    def get_match_odds(self, match_id: str):
        return self._active_provider.get_match_odds(match_id)

    def get_odds_history(self, match_id: str):
        try:
            return self._active_provider.get_odds_history(match_id)
        except Exception:
            return OddsHistory(match_id=match_id, history={})

    def _activate(self, provider: BaseProvider) -> None:
        self._active_provider = provider
        self.provider_used = getattr(provider, "provider_name", getattr(provider, "name", "unknown"))
        self.resolved_provider_name = self.provider_used

    def _format_fallback_warning(self, exc: Exception) -> str:
        reason = self._short_error(exc)
        primary_name = getattr(self.primary, "provider_name", getattr(self.primary, "name", "primary"))
        fallback_name = getattr(self.fallback, "provider_name", getattr(self.fallback, "name", "fallback"))
        return (
            f"{primary_name} provider failed: {reason}; fallback to {fallback_name}"
            "（实时公开数据暂不可用，已平静切换；mock 只用于演示流程，不会伪装成 Sporttery。）"
        )

    @staticmethod
    def _short_error(exc: Exception) -> str:
        text = str(exc).strip().replace("\n", " ")
        return text[:180] or exc.__class__.__name__
