export interface AssetInfo {
  internal_id: string;
  symbol: string;
  display_symbol: string;
  name: string;
  category: 'crypto' | 'equity' | 'tokenized_equity' | 'etf' | 'index_reference';
  provider: string;
  provider_symbol: string;
  quote_currency: string;
  underlying_symbol: string | null;
  underlying_name: string | null;
  venue: string;
  market_status: string;
  tradable_on_provider: boolean;
  metadata: Record<string, any>;
}

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
  data_status?: string;
}

export interface NormalizedEquityQuote {
  symbol: string;
  name: string;
  asset_type: string;
  provider: string;
  price: string | null;
  previous_close: string | null;
  open_price: string | null;
  high: string | null;
  low: string | null;
  change_abs: string | null;
  change_pct: number | null;
  volume: string | null;
  currency: string;
  market_timestamp: string | null;
  retrieved_at: string;
  market_state: 'open' | 'closed';
  data_status: 'live' | 'cached' | 'stale' | 'unavailable' | 'provider_not_configured';
}

export interface NormalizedTokenizedEquityQuote {
  symbol: string;
  display_symbol: string;
  name: string;
  asset_type: string;
  provider: string;
  provider_symbol: string;
  underlying_symbol: string;
  underlying_name: string;
  price: string | null;
  open_24h: string | null;
  high_24h: string | null;
  low_24h: string | null;
  volume_24h: string | null;
  quote_volume_24h: string | null;
  change_24h_abs: string | null;
  change_24h_pct: number | null;
  quote_currency: string;
  tokenized_label: string;
  timestamp: string | null;
  retrieved_at: string;
  data_status: 'live' | 'cached' | 'stale' | 'unavailable';
}

export interface EquityComparisonResponse {
  underlying_symbol: string;
  underlying_name: string;
  comparison_available: boolean;
  unavailability_reason: string | null;
  underlying_price: string | null;
  underlying_provider: string;
  underlying_data_status: string;
  underlying_market_state: string;
  underlying_timestamp: string | null;
  tokenized_counterpart_available: boolean;
  tokenized_symbol: string | null;
  tokenized_provider: string | null;
  tokenized_data_status: string | null;
  tokenized_price: string | null;
  tokenized_timestamp: string | null;
  price_difference_abs: string | null;
  price_difference_pct: number | null;
  comparison_label: string;
  disclaimer: string;
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

// News Intelligence Types (Phase 2B)
export interface RelatedAsset {
  symbol: string;
  display_symbol: string;
  name: string | null;
  asset_type: 'crypto' | 'equity';
  relationship_type: 'primary' | 'secondary' | 'tokenized_exposure';
  tokenized_symbol: string | null;
}

export interface NewsArticle {
  id: string;
  external_id: string | null;
  headline: string;
  summary: string | null;
  source: string;
  publisher: string | null;
  url: string;
  published_at: string;
  retrieved_at: string;
  category: 'general' | 'crypto' | 'company' | 'macro' | 'regulation' | 'earnings' | 'technology' | 'monetary_policy' | 'etf_institutional';
  related_assets: RelatedAsset[];
  related_companies: string[];
  relevance_score: number;
  sentiment_label: 'positive' | 'neutral' | 'negative' | 'mixed' | 'unknown';
  sentiment_score: number;
  impact_level: 'low' | 'medium' | 'high' | 'unknown';
  is_portfolio_relevant: boolean;
  portfolio_asset_match: string | null;
  duplicate_count: number;
  data_status: 'live' | 'cached' | 'stale' | 'unavailable' | 'provider_not_configured';
}

export interface NewsListResponse {
  articles: NewsArticle[];
  total_count: number;
  portfolio_relevant_count: number;
  last_collected_at: string | null;
  data_status: 'live' | 'cached' | 'stale' | 'unavailable' | 'provider_not_configured';
}

export interface NewsStatusResponse {
  configured_sources: string[];
  active_sources: string[];
  total_cached_articles: number;
  last_successful_collection: string | null;
  provider_statuses: Record<string, any>;
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

export async function fetchSupportedAssets(type?: string, query?: string): Promise<AssetInfo[]> {
  const params = new URLSearchParams();
  if (type) params.append('type', type);
  if (query) params.append('query', query);
  const queryStr = params.toString() ? `?${params.toString()}` : '';

  const res = await fetch(`${API_BASE_URL}/api/v1/markets/assets${queryStr}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch assets: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchEquities(): Promise<NormalizedEquityQuote[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/markets/equities`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch equities: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchEquityQuote(symbol: string): Promise<NormalizedEquityQuote> {
  const res = await fetch(`${API_BASE_URL}/api/v1/markets/equities/${symbol}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch quote for ${symbol}: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchTokenizedEquities(): Promise<NormalizedTokenizedEquityQuote[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/markets/tokenized-equities`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch tokenized equities: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchTokenizedEquityQuote(symbol: string): Promise<NormalizedTokenizedEquityQuote> {
  const res = await fetch(`${API_BASE_URL}/api/v1/markets/tokenized-equities/${symbol}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch tokenized quote for ${symbol}: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchEquityComparison(underlyingSymbol: string): Promise<EquityComparisonResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/markets/equity-comparison/${underlyingSymbol}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch comparison for ${underlyingSymbol}: HTTP ${res.status}`);
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

// News Intelligence API functions
export async function fetchNewsFeed(params?: {
  category?: string;
  asset?: string;
  source?: string;
  sentiment?: string;
  impact?: string;
  portfolio_only?: boolean;
  limit?: number;
  offset?: number;
}): Promise<NewsListResponse> {
  const query = new URLSearchParams();
  if (params?.category) query.append('category', params.category);
  if (params?.asset) query.append('asset', params.asset);
  if (params?.source) query.append('source', params.source);
  if (params?.sentiment) query.append('sentiment', params.sentiment);
  if (params?.impact) query.append('impact', params.impact);
  if (params?.portfolio_only) query.append('portfolio_only', 'true');
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('offset', params.offset.toString());

  const queryStr = query.toString() ? `?${query.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/api/v1/news${queryStr}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch news feed: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchNewsForAsset(symbol: string, limit: number = 20): Promise<NewsListResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/news/assets/${symbol}?limit=${limit}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch news for asset ${symbol}: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchPortfolioNews(limit: number = 20): Promise<NewsListResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/news/portfolio?limit=${limit}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch portfolio news: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchNewsStatus(): Promise<NewsStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/news/status`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch news status: HTTP ${res.status}`);
  }
  return res.json();
}
