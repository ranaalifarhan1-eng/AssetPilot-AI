from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.modules.market_data.cache import MarketDataCache, global_cache
from app.modules.market_data.exceptions import InvalidAssetError, InvalidTimeframeError, ProviderUnavailableError
from app.modules.market_data.okx_provider import SUPPORTED_ASSETS_MAP, TIMEFRAME_MAP
from app.modules.market_data.service import MarketDataService
from app.modules.technical_analysis.indicators import atr, bollinger, ema, last_swing, macd, rate_of_change, rsi, sma
from app.modules.technical_analysis.schemas import (
    MomentumEvidence, MultiTimeframeResponse, StructureEvidence, TechnicalAnalysisResponse,
    TimeframeSummary, TrendEvidence, VolatilityEvidence, VolumeEvidence,
)

SUPPORTED_TIMEFRAMES = ("5m", "15m", "1H", "4H", "1D")
MULTI_TIMEFRAMES = ("15m", "1H", "4H", "1D")
MIN_ANALYSIS_CANDLES = 50


def _rounded(value: Optional[float], digits: int = 6) -> Optional[float]:
    return round(value, digits) if value is not None else None


def _pct(current: float, reference: Optional[float]) -> Optional[float]:
    if reference in (None, 0):
        return None
    return ((current / reference) - 1.0) * 100.0


class TechnicalAnalysisService:
    def __init__(self, market_service: Optional[MarketDataService] = None, cache: Optional[MarketDataCache] = None):
        self.market_service = market_service or MarketDataService()
        self.cache = cache or global_cache

    async def analyze(self, symbol: str, timeframe: str = "1H") -> TechnicalAnalysisResponse:
        symbol = symbol.upper()
        if symbol not in SUPPORTED_ASSETS_MAP:
            raise InvalidAssetError(symbol)
        if timeframe not in SUPPORTED_TIMEFRAMES or timeframe not in TIMEFRAME_MAP:
            raise InvalidTimeframeError(timeframe)

        source = await self.market_service.get_candles(symbol, timeframe, 300)
        candles = self._normalize_candles(source.candles)
        source_updated = candles[-1].timestamp if candles else None
        source_status = source.data_status
        if not candles:
            return self._insufficient(symbol, timeframe, source.provider, source_status, 0, None)

        cache_key = f"technical:{symbol}:{timeframe}:{source_updated.isoformat()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached.model_copy(update={"data_status": source_status, "source_data_status": source_status})

        if len(candles) < MIN_ANALYSIS_CANDLES:
            result = self._insufficient(symbol, timeframe, source.provider, source_status, len(candles), source_updated)
            await self.cache.set(cache_key, result, ttl=30.0)
            return result

        closes = [float(c.close) for c in candles]
        highs = [float(c.high) for c in candles]
        lows = [float(c.low) for c in candles]
        volumes = [float(c.volume) for c in candles]
        current = closes[-1]

        sma20, sma50, sma200 = sma(closes, 20), sma(closes, 50), sma(closes, 200)
        ema12, ema26, ema50 = ema(closes, 12), ema(closes, 26), ema(closes, 50)
        rsi14 = rsi(closes, 14)
        macd_line, signal_line, histogram = macd(closes)
        roc10 = rate_of_change(closes, 10)
        atr14 = atr(highs, lows, closes, 14)
        bb_upper, bb_middle, bb_lower = bollinger(closes, 20, 2.0)
        atr_pct = (atr14 / current * 100.0) if atr14 is not None and current else None
        bandwidth = ((bb_upper - bb_lower) / bb_middle * 100.0) if bb_upper is not None and bb_lower is not None and bb_middle else None
        rolling_high, rolling_low = max(highs[-20:]), min(lows[-20:])
        avg_volume = sma(volumes, 20)

        result = TechnicalAnalysisResponse(
            asset=symbol, provider_symbol=SUPPORTED_ASSETS_MAP[symbol].provider_symbol,
            timeframe=timeframe, provider=source.provider, data_status=source_status,
            source_data_status=source_status, candles_used=len(candles), source_last_updated=source_updated,
            analysis_as_of=source_updated, analysis_computed_at=datetime.now(timezone.utc), current_price=_rounded(current),
            trend=TrendEvidence(
                state=self._trend_state(current, sma20, sma50), sma_20=_rounded(sma20), sma_50=_rounded(sma50),
                sma_200=_rounded(sma200), ema_12=_rounded(ema12), ema_26=_rounded(ema26), ema_50=_rounded(ema50),
                price_vs_sma_20_pct=_rounded(_pct(current, sma20), 3), price_vs_sma_50_pct=_rounded(_pct(current, sma50), 3),
            ),
            momentum=MomentumEvidence(
                state=self._momentum_state(rsi14, histogram), rsi_14=_rounded(rsi14, 3),
                rsi_state=self._rsi_state(rsi14), macd=_rounded(macd_line), signal=_rounded(signal_line),
                histogram=_rounded(histogram), macd_state=self._macd_state(histogram), roc_10_pct=_rounded(roc10, 3),
            ),
            volatility=VolatilityEvidence(
                state=self._volatility_state(atr_pct), atr_14=_rounded(atr14), atr_pct=_rounded(atr_pct, 3),
                bollinger_upper=_rounded(bb_upper), bollinger_middle=_rounded(bb_middle), bollinger_lower=_rounded(bb_lower),
                bollinger_bandwidth_pct=_rounded(bandwidth, 3),
            ),
            structure=StructureEvidence(
                recent_swing_high=_rounded(last_swing(highs, True) or rolling_high),
                recent_swing_low=_rounded(last_swing(lows, False) or rolling_low),
                rolling_high_20=_rounded(rolling_high), rolling_low_20=_rounded(rolling_low),
                distance_from_high_pct=_rounded(_pct(current, rolling_high), 3),
                distance_from_low_pct=_rounded(_pct(current, rolling_low), 3),
            ),
            volume=VolumeEvidence(
                current=_rounded(volumes[-1]), average_20=_rounded(avg_volume),
                relative_volume=_rounded(volumes[-1] / avg_volume, 3) if avg_volume else None,
            ),
        )
        await self.cache.set(cache_key, result, ttl=300.0)
        return result

    async def analyze_multi_timeframe(self, symbol: str) -> MultiTimeframeResponse:
        if symbol.upper() not in SUPPORTED_ASSETS_MAP:
            raise InvalidAssetError(symbol)
        results = await asyncio.gather(*(self.analyze(symbol, timeframe) for timeframe in MULTI_TIMEFRAMES), return_exceptions=True)
        summaries = {}
        for timeframe, result in zip(MULTI_TIMEFRAMES, results):
            if isinstance(result, TechnicalAnalysisResponse):
                summaries[timeframe] = TimeframeSummary(
                    timeframe=timeframe, data_status=result.data_status, trend_state=result.trend.state,
                    momentum_state=result.momentum.state, volatility_state=result.volatility.state,
                    rsi_14=result.momentum.rsi_14, analysis_as_of=result.analysis_as_of,
                )
            else:
                summaries[timeframe] = TimeframeSummary(
                    timeframe=timeframe, data_status="unavailable", trend_state="insufficient_data",
                    momentum_state="insufficient_data", volatility_state="insufficient_data",
                )
        return MultiTimeframeResponse(
            asset=symbol.upper(), timeframe_alignment=self._alignment([item.trend_state for item in summaries.values()]),
            summaries=summaries, computed_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _normalize_candles(candles):
        unique = {candle.timestamp: candle for candle in candles}
        return [unique[key] for key in sorted(unique)]

    @staticmethod
    def _trend_state(price, sma20, sma50):
        if sma20 is None or sma50 is None:
            return "insufficient_data"
        distance = _pct(price, sma50) or 0.0
        if price > sma20 > sma50:
            return "strong_uptrend" if distance >= 2.0 else "uptrend"
        if price < sma20 < sma50:
            return "strong_downtrend" if distance <= -2.0 else "downtrend"
        return "range"

    @staticmethod
    def _momentum_state(rsi_value, histogram):
        if rsi_value is None or histogram is None:
            return "insufficient_data"
        if rsi_value >= 60 and histogram > 0:
            return "strong_positive"
        if rsi_value >= 50 and histogram >= 0:
            return "positive"
        if rsi_value <= 40 and histogram < 0:
            return "strong_negative"
        if rsi_value < 50 and histogram <= 0:
            return "negative"
        return "neutral"

    @staticmethod
    def _volatility_state(atr_pct):
        if atr_pct is None:
            return "insufficient_data"
        if atr_pct < 1.0:
            return "low"
        if atr_pct < 2.5:
            return "normal"
        if atr_pct < 5.0:
            return "elevated"
        return "high"

    @staticmethod
    def _rsi_state(value):
        if value is None:
            return "insufficient_data"
        return "oversold" if value < 30 else "overbought" if value > 70 else "neutral"

    @staticmethod
    def _macd_state(histogram):
        if histogram is None:
            return "insufficient_data"
        if abs(histogram) < 1e-12:
            return "neutral"
        return "bullish" if histogram > 0 else "bearish"

    @staticmethod
    def _alignment(states):
        valid = [state for state in states if state != "insufficient_data"]
        if len(valid) < 2:
            return "insufficient_data"
        directions = [1 if "uptrend" in state else -1 if "downtrend" in state else 0 for state in valid]
        if all(direction == directions[0] and direction != 0 for direction in directions):
            return "strongly_aligned" if len(valid) == len(states) else "aligned"
        if 1 in directions and -1 in directions:
            return "conflicting"
        return "mixed"

    @staticmethod
    def _insufficient(symbol, timeframe, provider, source_status, count, source_updated):
        return TechnicalAnalysisResponse(
            asset=symbol, provider_symbol=SUPPORTED_ASSETS_MAP[symbol].provider_symbol, timeframe=timeframe,
            provider=provider, data_status="insufficient_data", source_data_status=source_status, candles_used=count,
            source_last_updated=source_updated, analysis_as_of=source_updated, analysis_computed_at=datetime.now(timezone.utc),
            trend=TrendEvidence(state="insufficient_data"), momentum=MomentumEvidence(state="insufficient_data"),
            volatility=VolatilityEvidence(state="insufficient_data"), structure=StructureEvidence(), volume=VolumeEvidence(),
        )
