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

export interface AccountSourceBalance {
  source: string;
  balance: string;
  available: string;
  frozen: string;
}

export interface PortfolioAsset {
  symbol: string;
  name: string;
  total_balance: string;
  available_balance: string;
  frozen_balance: string;
  account_sources: AccountSourceBalance[];
  price_usdt: string | null;
  estimated_value_usdt: string | null;
  valuation_available: boolean;
  allocation_pct: number;
}

export interface PortfolioSummary {
  total_value_usdt: string;
  assets: PortfolioAsset[];
  asset_count: number;
  last_synced_at: string | null;
  provider: string;
  data_status: 'configured' | 'unconfigured' | 'error';
  error_message: string | null;
}

export interface PortfolioStatusResponse {
  configured: boolean;
  provider: string;
  read_only_expected: boolean;
  last_successful_sync: string | null;
  connection_status: 'connected' | 'unconfigured' | 'error';
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

export async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const res = await fetch(`${API_BASE_URL}/api/v1/portfolio`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch portfolio summary: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchPortfolioStatus(): Promise<PortfolioStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/portfolio/status`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch portfolio status: HTTP ${res.status}`);
  }
  return res.json();
}
