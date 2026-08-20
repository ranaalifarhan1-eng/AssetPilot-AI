export interface NormalizedTicker {
  symbol: string;
  provider_symbol: string;
  name: string;
  price: string;
  open_24h: string;
  high_24h: string;
  low_24h: string;
  volume_24h: string;
  quote_volume_24h: string;
  change_24h_abs: string;
  change_24h_pct: number;
  timestamp: string;
  provider: string;
}

export interface MarketOverviewResponse {
  updated_at: string;
  provider: string;
  tickers: NormalizedTicker[];
}

export interface NormalizedCandle {
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

export interface CandleResponse {
  symbol: string;
  timeframe: string;
  provider: string;
  candles: NormalizedCandle[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export async function fetchMarketOverview(): Promise<MarketOverviewResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/markets/overview`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch market overview: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchAssetTicker(symbol: string): Promise<NormalizedTicker> {
  const res = await fetch(`${API_BASE_URL}/api/v1/markets/${symbol}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch ticker for ${symbol}: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchAssetCandles(
  symbol: string,
  timeframe: string = '1H',
  limit: number = 100
): Promise<CandleResponse> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/markets/${symbol}/candles?timeframe=${timeframe}&limit=${limit}`,
    {
      cache: 'no-store',
    }
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch candles for ${symbol}: HTTP ${res.status}`);
  }
  return res.json();
}
