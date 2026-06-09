from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class BankrollState:
    initial_bankroll: float
    current_bankroll: float
    peak_bankroll: float
    max_drawdown: float
    total_staked: float
    total_profit: float

    def to_dict(self) -> dict:
        return asdict(self)


def create_bankroll(initial_bankroll: float = 10000.0) -> BankrollState:
    value = max(0.0, float(initial_bankroll))
    return BankrollState(
        initial_bankroll=value,
        current_bankroll=value,
        peak_bankroll=value,
        max_drawdown=0.0,
        total_staked=0.0,
        total_profit=0.0,
    )


def apply_settlement(bankroll: BankrollState, stake: float, profit: float) -> BankrollState:
    stake_value = max(0.0, float(stake or 0.0))
    profit_value = float(profit or 0.0)
    current = max(0.0, bankroll.current_bankroll + profit_value)
    peak = max(bankroll.peak_bankroll, current)
    drawdown = calculate_drawdown(current, peak)
    return BankrollState(
        initial_bankroll=bankroll.initial_bankroll,
        current_bankroll=round(current, 2),
        peak_bankroll=round(peak, 2),
        max_drawdown=max(bankroll.max_drawdown, drawdown),
        total_staked=round(bankroll.total_staked + stake_value, 2),
        total_profit=round(bankroll.total_profit + profit_value, 2),
    )


def calculate_drawdown(current: float, peak: float) -> float:
    peak_value = float(peak or 0.0)
    if peak_value <= 0:
        return 0.0
    return max(0.0, round((peak_value - float(current or 0.0)) / peak_value, 6))
