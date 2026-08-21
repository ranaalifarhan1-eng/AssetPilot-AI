"""Dependency-free deterministic technical indicator calculations."""

from __future__ import annotations

from math import sqrt
from typing import Optional, Sequence


def sma(values: Sequence[float], period: int) -> Optional[float]:
    if period <= 0 or len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema_series(values: Sequence[float], period: int) -> list[float]:
    if period <= 0 or len(values) < period:
        return []
    seed = sum(values[:period]) / period
    result = [seed]
    multiplier = 2.0 / (period + 1.0)
    for value in values[period:]:
        result.append((value - result[-1]) * multiplier + result[-1])
    return result


def ema(values: Sequence[float], period: int) -> Optional[float]:
    series = ema_series(values, period)
    return series[-1] if series else None


def rsi(values: Sequence[float], period: int = 14) -> Optional[float]:
    if len(values) < period + 1:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    return 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))


def macd(values: Sequence[float]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    if len(values) < 35:
        return None, None, None
    fast = ema_series(values, 12)
    slow = ema_series(values, 26)
    # EMA series start at different source offsets; align both to the slow series.
    aligned_fast = fast[len(fast) - len(slow):]
    line_series = [f - s for f, s in zip(aligned_fast, slow)]
    signal_series = ema_series(line_series, 9)
    if not signal_series:
        return None, None, None
    line = line_series[-1]
    signal = signal_series[-1]
    return line, signal, line - signal


def rate_of_change(values: Sequence[float], period: int = 10) -> Optional[float]:
    if len(values) < period + 1 or values[-period - 1] == 0:
        return None
    return ((values[-1] / values[-period - 1]) - 1.0) * 100.0


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14) -> Optional[float]:
    if len(closes) < period + 1 or not (len(highs) == len(lows) == len(closes)):
        return None
    true_ranges = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(1, len(closes))
    ]
    value = sum(true_ranges[:period]) / period
    for current in true_ranges[period:]:
        value = ((value * (period - 1)) + current) / period
    return value


def bollinger(values: Sequence[float], period: int = 20, deviations: float = 2.0) -> tuple[Optional[float], Optional[float], Optional[float]]:
    middle = sma(values, period)
    if middle is None:
        return None, None, None
    window = values[-period:]
    stddev = sqrt(sum((value - middle) ** 2 for value in window) / period)
    return middle + deviations * stddev, middle, middle - deviations * stddev


def last_swing(values: Sequence[float], high: bool, radius: int = 2) -> Optional[float]:
    if len(values) < radius * 2 + 1:
        return None
    for index in range(len(values) - radius - 1, radius - 1, -1):
        window = values[index - radius:index + radius + 1]
        if (high and values[index] == max(window)) or (not high and values[index] == min(window)):
            return values[index]
    return None
