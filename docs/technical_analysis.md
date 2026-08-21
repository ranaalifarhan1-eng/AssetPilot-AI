# Phase 3A Technical Intelligence

AssetPilot's technical layer converts verified OKX SPOT OHLCV candles for BTC, ETH, and SOL into deterministic descriptive evidence. It does not produce recommendations, price targets, forecasts, or trading actions.

## Inputs and timeframes

- Provider: OKX public SPOT through the existing normalized candle pipeline.
- Timeframes: `5m`, `15m`, `1H`, `4H`, and `1D`.
- Candles are sorted oldest-to-newest and duplicate timestamps are reduced to one observation.
- No candles are fabricated, interpolated, or forward-filled.
- Fewer than 50 unique candles returns `insufficient_data`. SMA 200 remains null until 200 observations exist.

## Indicators

- SMA: arithmetic mean over 20, 50, and 200 closing prices.
- EMA: arithmetic seed followed by multiplier `2 / (period + 1)` for periods 12, 26, and 50.
- RSI 14: Wilder-smoothed gains and losses. A flat series is defined as RSI 50.
- MACD: EMA 12 minus EMA 26, with EMA 9 signal and line-minus-signal histogram.
- ROC 10: `(current / close_10_periods_ago - 1) * 100`.
- ATR 14: Wilder-smoothed true range.
- Bollinger Bands 20/2: SMA 20 plus/minus two population standard deviations. Bandwidth is `(upper-lower)/middle * 100`.
- Structure: most recent two-candle-radius local swing plus rolling 20-period high and low.
- Volume: current volume, SMA 20 volume, and current/average relative volume. Relative volume is null when average volume is zero.

## Descriptive states

Trend:

- `strong_uptrend`: price > SMA20 > SMA50 and price is at least 2% above SMA50.
- `uptrend`: price > SMA20 > SMA50 without the strong threshold.
- `strong_downtrend`: price < SMA20 < SMA50 and price is at least 2% below SMA50.
- `downtrend`: price < SMA20 < SMA50 without the strong threshold.
- `range`: other fully calculated configurations.

Momentum:

- `strong_positive`: RSI >= 60 and MACD histogram > 0.
- `positive`: RSI >= 50 and histogram >= 0.
- `strong_negative`: RSI <= 40 and histogram < 0.
- `negative`: RSI < 50 and histogram <= 0.
- `neutral`: mixed momentum evidence.

RSI is `oversold` below 30, `overbought` above 70, otherwise `neutral`. MACD is bullish or bearish by histogram sign, with an effectively zero histogram treated as neutral.

Volatility uses ATR as a percentage of price: below 1% is `low`, below 2.5% is `normal`, below 5% is `elevated`, and 5% or above is `high`.

## Multi-timeframe alignment

The compact endpoint compares `15m`, `1H`, `4H`, and `1D` trend direction:

- `strongly_aligned`: every timeframe has the same non-range direction.
- `aligned`: at least two available timeframes share the same direction while another is insufficient.
- `conflicting`: both uptrend and downtrend directions occur.
- `mixed`: available states contain range or partial directional agreement.
- `insufficient_data`: fewer than two timeframes can be evaluated.

Alignment is descriptive and is not a buy/sell instruction.

## Provenance and caching

`source_data_status` is copied from the candle response. `source_last_updated` and `analysis_as_of` identify the newest source candle; `analysis_computed_at` identifies calculation time. These timestamps are intentionally distinct.

Results are cached under `technical:{symbol}:{timeframe}:{latest_candle_timestamp}` for up to five minutes. The candle pipeline is still consulted first, and a reused calculation is relabeled with the current candle response provenance. A new candle timestamp creates a new cache key.

## API

- `GET /api/v1/technical/{symbol}?timeframe=1H`
- `GET /api/v1/technical/{symbol}/multi-timeframe`

Both endpoints are read-only. Technical states are quantitative descriptions, not investment recommendations.
