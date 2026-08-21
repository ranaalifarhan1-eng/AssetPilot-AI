from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.technical import technical_service
from app.main import app
from app.modules.market_data.cache import MarketDataCache
from app.modules.market_data.exceptions import ProviderUnavailableError
from app.modules.market_data.schemas import CandleResponse, NormalizedCandle
from app.modules.technical_analysis.indicators import atr, bollinger, ema, macd, rate_of_change, rsi, sma
from app.modules.technical_analysis.service import TechnicalAnalysisService

client = TestClient(app)


def make_candles(count=220, flat=False, reverse=False, duplicate_latest=False, zero_volume=False):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles = []
    for index in range(count):
        close = 100.0 if flat else 100.0 + index * 0.5 + (index % 7) * 0.1
        candles.append(NormalizedCandle(
            timestamp=start + timedelta(hours=index), open=str(close - 0.2), high=str(close + 1.0),
            low=str(close - 1.0), close=str(close), volume="0" if zero_volume else str(100 + index),
        ))
    if duplicate_latest:
        candles.append(candles[-1])
    return list(reversed(candles)) if reverse else candles


class FakeMarketService:
    def __init__(self, candles, status="live"):
        self.candles = candles
        self.status = status
        self.calls = 0

    async def get_candles(self, symbol, timeframe, limit):
        self.calls += 1
        return CandleResponse(symbol=symbol, timeframe=timeframe, provider="OKX", candles=self.candles, data_status=self.status)


def test_indicator_numerical_foundations():
    assert sma(list(range(1, 21)), 20) == pytest.approx(10.5)
    assert ema([5.0] * 20, 12) == pytest.approx(5.0)
    assert rsi([5.0] * 20, 14) == pytest.approx(50.0)
    assert rate_of_change([100.0] * 10 + [110.0], 10) == pytest.approx(10.0)
    upper, middle, lower = bollinger([5.0] * 20)
    assert (upper, middle, lower) == pytest.approx((5.0, 5.0, 5.0))
    assert atr([11.0] * 15, [9.0] * 15, [10.0] * 15, 14) == pytest.approx(2.0)


def test_macd_increasing_series_is_positive():
    line, signal, histogram = macd([float(value) for value in range(1, 80)])
    assert line is not None and line > 0
    assert signal is not None and signal > 0
    assert histogram == pytest.approx(line - signal)


@pytest.mark.asyncio
async def test_full_analysis_and_sma_200():
    service = TechnicalAnalysisService(FakeMarketService(make_candles()), MarketDataCache())
    result = await service.analyze("BTC", "1H")
    assert result.data_status == "live"
    assert result.candles_used == 220
    assert result.trend.sma_20 is not None
    assert result.trend.sma_50 is not None
    assert result.trend.sma_200 is not None
    assert result.momentum.rsi_14 is not None
    assert result.momentum.macd is not None
    assert result.volatility.atr_14 is not None
    assert result.volatility.bollinger_upper is not None
    assert result.structure.rolling_high_20 is not None
    assert result.volume.relative_volume is not None


@pytest.mark.asyncio
async def test_insufficient_history_is_explicit():
    service = TechnicalAnalysisService(FakeMarketService(make_candles(30)), MarketDataCache())
    result = await service.analyze("ETH", "4H")
    assert result.data_status == "insufficient_data"
    assert result.source_data_status == "live"
    assert result.trend.state == "insufficient_data"


@pytest.mark.asyncio
async def test_flat_price_and_zero_volume_are_safe():
    service = TechnicalAnalysisService(FakeMarketService(make_candles(flat=True, zero_volume=True)), MarketDataCache())
    result = await service.analyze("SOL", "1D")
    assert result.momentum.rsi_14 == pytest.approx(50.0)
    assert result.volume.relative_volume is None
    assert result.structure.distance_from_high_pct is not None


@pytest.mark.asyncio
async def test_reversed_and_duplicate_candles_are_normalized():
    candles = make_candles(reverse=True, duplicate_latest=True)
    service = TechnicalAnalysisService(FakeMarketService(candles), MarketDataCache())
    result = await service.analyze("BTC", "15m")
    assert result.candles_used == 220
    assert result.analysis_as_of == max(candle.timestamp for candle in candles)


@pytest.mark.asyncio
async def test_cached_source_provenance_is_preserved():
    service = TechnicalAnalysisService(FakeMarketService(make_candles(), status="cached"), MarketDataCache())
    result = await service.analyze("BTC", "1H")
    assert result.data_status == "cached"
    assert result.source_data_status == "cached"


@pytest.mark.asyncio
async def test_stale_source_provenance_is_preserved():
    service = TechnicalAnalysisService(FakeMarketService(make_candles(), status="stale"), MarketDataCache())
    result = await service.analyze("BTC", "4H")
    assert result.data_status == "stale"
    assert result.source_data_status == "stale"


@pytest.mark.asyncio
async def test_analysis_cache_reuses_same_latest_candle():
    market = FakeMarketService(make_candles())
    cache = MarketDataCache()
    service = TechnicalAnalysisService(market, cache)
    first = await service.analyze("BTC", "1H")
    market.status = "cached"
    second = await service.analyze("BTC", "1H")
    assert first.analysis_computed_at == second.analysis_computed_at
    assert second.data_status == "cached"


@pytest.mark.asyncio
async def test_multi_timeframe_alignment_is_descriptive():
    service = TechnicalAnalysisService(FakeMarketService(make_candles()), MarketDataCache())
    result = await service.analyze_multi_timeframe("BTC")
    assert set(result.summaries) == {"15m", "1H", "4H", "1D"}
    assert result.timeframe_alignment in {"strongly_aligned", "aligned", "mixed", "conflicting", "insufficient_data"}


def test_malformed_candle_rejected_by_normalized_schema():
    with pytest.raises(ValidationError):
        NormalizedCandle(timestamp=datetime.now(timezone.utc), open="1", high="2", low="0", volume="10")


def test_technical_api_and_validation():
    response = CandleResponse(symbol="BTC", timeframe="1H", provider="OKX", candles=make_candles(), data_status="live")
    with patch.object(technical_service.market_service, "get_candles", new=AsyncMock(return_value=response)):
        technical_service.cache = MarketDataCache()
        result = client.get("/api/v1/technical/BTC?timeframe=1H")
        assert result.status_code == 200
        assert result.json()["trend"]["state"] in {"uptrend", "strong_uptrend", "range"}
    assert client.get("/api/v1/technical/DOGE?timeframe=1H").status_code == 400
    assert client.get("/api/v1/technical/BTC?timeframe=2H").status_code == 400
    assert client.get("/api/v1/technical/DOGE/multi-timeframe").status_code == 400


def test_provider_failure_returns_503():
    with patch.object(
        technical_service.market_service, "get_candles",
        new=AsyncMock(side_effect=ProviderUnavailableError("OKX", "temporarily unavailable")),
    ):
        result = client.get("/api/v1/technical/BTC?timeframe=1H")
        assert result.status_code == 503
