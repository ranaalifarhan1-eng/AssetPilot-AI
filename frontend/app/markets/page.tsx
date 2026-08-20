'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';
import {
  fetchMarketOverview,
  fetchAssetCandles,
  fetchEquities,
  fetchTokenizedEquities,
  fetchEquityComparison,
  NormalizedTicker,
  NormalizedCandle,
  NormalizedEquityQuote,
  NormalizedTokenizedEquityQuote,
  EquityComparisonResponse,
} from '@/lib/api';
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertCircle,
  BarChart2,
  Clock,
  Layers,
  ArrowRightLeft,
  Building2,
  Coins,
  ShieldCheck,
  X,
  Info,
  Sliders,
} from 'lucide-react';

export default function MarketsPage() {
  const [activeTab, setActiveTab] = useState<'crypto' | 'stocks' | 'tokenized'>('crypto');

  // Crypto state
  const [tickers, setTickers] = useState<NormalizedTicker[]>([]);
  const [selectedCrypto, setSelectedCrypto] = useState<string>('BTC');
  const [candles, setCandles] = useState<NormalizedCandle[]>([]);
  const [timeframe, setTimeframe] = useState<string>('1H');
  const [cryptoLoading, setCryptoLoading] = useState<boolean>(true);
  const [chartLoading, setChartLoading] = useState<boolean>(false);

  // Stocks state
  const [equities, setEquities] = useState<NormalizedEquityQuote[]>([]);
  const [stocksLoading, setStocksLoading] = useState<boolean>(false);

  // Tokenized stocks state
  const [tokenizedEquities, setTokenizedEquities] = useState<NormalizedTokenizedEquityQuote[]>([]);
  const [tokenizedLoading, setTokenizedLoading] = useState<boolean>(false);

  // Comparison modal state
  const [comparisonModalSymbol, setComparisonModalSymbol] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<EquityComparisonResponse | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  // Load Crypto Overview
  const loadCryptoData = async () => {
    try {
      setCryptoLoading(true);
      setError(null);
      const data = await fetchMarketOverview();
      setTickers(data.tickers);
      setLastUpdated(new Date(data.updated_at).toLocaleTimeString());
    } catch (err: any) {
      console.error('Error fetching crypto market data:', err);
      setError('Crypto market data temporarily unavailable');
    } finally {
      setCryptoLoading(false);
    }
  };

  // Load Crypto Candles
  const loadCandles = async (sym: string, tf: string) => {
    try {
      setChartLoading(true);
      const data = await fetchAssetCandles(sym, tf, 50);
      setCandles(data.candles || []);
    } catch (err: any) {
      console.error(`Error loading candles for ${sym}:`, err);
      setCandles([]);
    } finally {
      setChartLoading(false);
    }
  };

  // Load Stocks
  const loadStocksData = async () => {
    try {
      setStocksLoading(true);
      setError(null);
      const data = await fetchEquities();
      setEquities(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: any) {
      console.error('Error fetching equities data:', err);
      setError('Traditional equity data temporarily unavailable');
    } finally {
      setStocksLoading(false);
    }
  };

  // Load Tokenized Stocks
  const loadTokenizedData = async () => {
    try {
      setTokenizedLoading(true);
      setError(null);
      const data = await fetchTokenizedEquities();
      setTokenizedEquities(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: any) {
      console.error('Error fetching tokenized equities data:', err);
      setError('OKX tokenized equity data temporarily unavailable');
    } finally {
      setTokenizedLoading(false);
    }
  };

  // Trigger comparison modal
  const openComparisonModal = async (underlyingSymbol: string) => {
    setComparisonModalSymbol(underlyingSymbol);
    setComparisonLoading(true);
    setComparisonData(null);
    try {
      const data = await fetchEquityComparison(underlyingSymbol);
      setComparisonData(data);
    } catch (err: any) {
      console.error('Error fetching comparison:', err);
    } finally {
      setComparisonLoading(false);
    }
  };

  useEffect(() => {
    loadCryptoData();
  }, []);

  useEffect(() => {
    if (activeTab === 'crypto') {
      loadCandles(selectedCrypto, timeframe);
    } else if (activeTab === 'stocks' && equities.length === 0) {
      loadStocksData();
    } else if (activeTab === 'tokenized' && tokenizedEquities.length === 0) {
      loadTokenizedData();
    }
  }, [activeTab, selectedCrypto, timeframe]);

  const isFinnhubUnconfigured = equities.length > 0 && equities.every(e => e.data_status === 'provider_not_configured');

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-100">Multi-Asset Market Explorer</h2>
          <p className="text-xs text-gray-400 mt-1">
            Normalized live market feeds across Core Crypto, US Equities, and OKX Tokenized Equities.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-[11px] font-mono text-gray-400 flex items-center gap-1 bg-gray-900/60 px-2.5 py-1 rounded border border-gray-800">
              <Clock className="h-3 w-3" /> Updated {lastUpdated}
            </span>
          )}

          <button
            onClick={() => {
              if (activeTab === 'crypto') loadCryptoData();
              if (activeTab === 'stocks') loadStocksData();
              if (activeTab === 'tokenized') loadTokenizedData();
            }}
            className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 rounded-lg transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`h-4 w-4 ${cryptoLoading || stocksLoading || tokenizedLoading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/40 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-gray-800 pb-2 text-xs font-medium">
        <button
          onClick={() => setActiveTab('crypto')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'crypto'
              ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900/60'
          }`}
        >
          <Coins className="h-4 w-4" />
          <span>Crypto (OKX)</span>
          <Badge variant="blue" size="sm">3 Assets</Badge>
        </button>

        <button
          onClick={() => setActiveTab('stocks')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'stocks'
              ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/40'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900/60'
          }`}
        >
          <Building2 className="h-4 w-4" />
          <span>US Equities (Finnhub)</span>
          <Badge variant="green" size="sm">10 Stocks</Badge>
        </button>

        <button
          onClick={() => setActiveTab('tokenized')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg transition-colors ${
            activeTab === 'tokenized'
              ? 'bg-purple-600/20 text-purple-400 border border-purple-500/40'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900/60'
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Tokenized Stocks (OKX)</span>
          <Badge variant="purple" size="sm">xStocks</Badge>
        </button>
      </div>

      {/* TAB 1: CRYPTO VIEW */}
      {activeTab === 'crypto' && (
        <div className="space-y-6">
          {/* Asset Tickers Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {tickers.map((ticker) => {
              const isSelected = selectedCrypto === ticker.symbol;
              const isPositive = ticker.change_24h_pct >= 0;

              return (
                <div
                  key={ticker.symbol}
                  onClick={() => setSelectedCrypto(ticker.symbol)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-950/20 border-blue-500/50 shadow-lg shadow-blue-950/40'
                      : 'bg-gray-900/60 border-gray-800/80 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-bold text-gray-100">{ticker.symbol}/USDT</span>
                      <span className="text-xs text-gray-400 block font-mono">{ticker.name}</span>
                    </div>
                    <Badge variant={isPositive ? 'green' : 'red'} size="sm">
                      {isPositive ? `+${ticker.change_24h_pct}%` : `${ticker.change_24h_pct}%`}
                    </Badge>
                  </div>

                  <div className="mt-3 flex items-baseline justify-between">
                    <span className="text-2xl font-bold text-gray-100 font-mono">
                      ${parseFloat(ticker.price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                    <span className="text-xs text-gray-400 font-mono">
                      Vol: ${parseFloat(ticker.quote_volume_24h).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                  </div>

                  <div className="mt-2 text-[10px] text-gray-500 font-mono flex items-center justify-between border-t border-gray-800/40 pt-1.5">
                    <span>Provider: <strong>{ticker.provider}</strong></span>
                    <span>24h Range: ${parseFloat(ticker.low_24h).toLocaleString()} - ${parseFloat(ticker.high_24h).toLocaleString()}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Interactive Chart */}
          <Card
            title={`${selectedCrypto}/USDT Market Candles`}
            subtitle="Normalized historical OHLCV chart feed"
            badge={<Badge variant="blue" size="sm">OKX PUBLIC SPOT</Badge>}
            action={
              <div className="flex items-center gap-1 bg-gray-900 border border-gray-800 p-0.5 rounded-lg text-xs font-mono">
                {['5m', '15m', '1H', '4H', '1D'].map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setTimeframe(tf)}
                    className={`px-2 py-0.5 rounded ${
                      timeframe === tf ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            }
          >
            {chartLoading ? (
              <div className="h-64 flex items-center justify-center text-xs text-gray-400 font-mono">
                Loading {selectedCrypto} candles...
              </div>
            ) : candles.length > 0 ? (
              <div className="space-y-4">
                {/* SVG Visualizer */}
                <div className="h-56 w-full bg-gray-950/60 rounded-lg border border-gray-800/80 p-3 relative flex items-end">
                  <div className="absolute top-2 left-3 text-[11px] font-mono text-gray-400 flex items-center gap-2">
                    <BarChart2 className="h-3.5 w-3.5 text-blue-400" />
                    <span>OHLCV • {candles.length} periods ({timeframe})</span>
                  </div>

                  <div className="w-full h-44 flex items-end justify-between gap-1 pt-6">
                    {candles.slice(-40).map((c, i) => {
                      const op = parseFloat(c.open);
                      const cl = parseFloat(c.close);
                      const isUp = cl >= op;
                      const minP = Math.min(...candles.map((x) => parseFloat(x.low)));
                      const maxP = Math.max(...candles.map((x) => parseFloat(x.high)));
                      const range = maxP - minP || 1;
                      const heightPct = Math.max(8, ((Math.max(op, cl) - minP) / range) * 100);

                      return (
                        <div key={i} className="flex-1 flex flex-col items-center justify-end h-full group relative">
                          <div
                            className={`w-full rounded-t-sm transition-all ${
                              isUp ? 'bg-emerald-500/80 hover:bg-emerald-400' : 'bg-red-500/80 hover:bg-red-400'
                            }`}
                            style={{ height: `${heightPct}%` }}
                          ></div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-xs text-gray-500 font-mono">
                No candle history available.
              </div>
            )}
          </Card>
        </div>
      )}

      {/* TAB 2: TRADITIONAL US EQUITIES */}
      {activeTab === 'stocks' && (
        <div className="space-y-4">
          {isFinnhubUnconfigured && (
            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 text-xs text-amber-300 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-amber-200">
                <Sliders className="h-4 w-4 text-amber-400" />
                <span>US Equity Live Data Provider Not Configured</span>
              </div>
              <p className="text-amber-300/80">
                To enable live US stocks reference pricing, configure <code>FINNHUB_API_KEY</code> in <code>backend/.env</code>.
                AssetPilot AI enforces zero data fabrication: no synthetic or mock stock prices are displayed.
              </p>
            </div>
          )}

          <div className="p-3.5 rounded-xl bg-gray-900/60 border border-gray-800/80 flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-emerald-400" />
              <span>US Equity Reference Data Provider: <strong>Finnhub</strong> • Regular Hours 09:30 - 16:00 EST</span>
            </span>
            <span className="font-mono text-[11px] text-gray-500">10 Core US Stocks</span>
          </div>

          <Card
            title="Traditional US Equities Universe"
            subtitle="Live market quotes & tokenized counterpart indicators (Strict zero-fabrication mode)"
            badge={<Badge variant={isFinnhubUnconfigured ? 'gray' : 'green'} size="sm">
              {isFinnhubUnconfigured ? 'PROVIDER NOT CONFIGURED' : 'US EQUITIES'}
            </Badge>}
          >
            {stocksLoading ? (
              <div className="p-8 text-center text-xs text-gray-400 font-mono">Loading US Equities quotes...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-900/80 text-gray-400 font-mono uppercase text-[10px] border-b border-gray-800">
                    <tr>
                      <th className="py-3 px-4">Symbol</th>
                      <th className="py-3 px-4">Company Name</th>
                      <th className="py-3 px-4">Price (USD)</th>
                      <th className="py-3 px-4">Daily Change</th>
                      <th className="py-3 px-4">Market State</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/60 font-mono">
                    {equities.map((eq) => {
                      const isPositive = (eq.change_pct || 0) >= 0;
                      return (
                        <tr key={eq.symbol} className="hover:bg-gray-900/40 transition-colors">
                          <td className="py-3 px-4 font-bold text-gray-100 font-sans">{eq.symbol}</td>
                          <td className="py-3 px-4 text-gray-300 font-sans">{eq.name}</td>
                          <td className="py-3 px-4 font-bold text-gray-100">
                            {eq.price ? `$${parseFloat(eq.price).toFixed(2)}` : (
                              <span className="text-gray-500 text-[11px] font-sans">Provider Unconfigured</span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            {eq.change_pct !== null && eq.change_pct !== undefined ? (
                              <span className={`flex items-center gap-1 font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                                {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                {isPositive ? `+${eq.change_pct}%` : `${eq.change_pct}%`}
                              </span>
                            ) : (
                              <span className="text-gray-500">—</span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <Badge variant={eq.market_state === 'open' ? 'green' : 'gray'} size="sm">
                              {eq.market_state.toUpperCase()}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => openComparisonModal(eq.symbol)}
                              className="px-2.5 py-1 rounded bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 border border-blue-500/30 text-[11px] font-sans transition-colors inline-flex items-center gap-1"
                            >
                              <ArrowRightLeft className="h-3 w-3" /> Compare with xStock
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* TAB 3: OKX TOKENIZED STOCKS */}
      {activeTab === 'tokenized' && (
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-800/30 flex items-center justify-between text-xs text-purple-300">
            <span className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-purple-400" />
              <span>OKX Tokenized Equity SPOT Feeds • Dynamically Discovered xStocks</span>
            </span>
            <span className="font-mono text-[11px] text-purple-400">Strictly Non-Custodial Reference Feeds</span>
          </div>

          <Card
            title="OKX Tokenized Equities (xStocks)"
            subtitle="Live OKX SPOT market feeds for tokenized equity representations"
            badge={<Badge variant="purple" size="sm">TOKENIZED EQUITIES • OKX</Badge>}
          >
            {tokenizedLoading ? (
              <div className="p-8 text-center text-xs text-gray-400 font-mono">Discovering OKX tokenized stock tickers...</div>
            ) : tokenizedEquities.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-900/80 text-gray-400 font-mono uppercase text-[10px] border-b border-gray-800">
                    <tr>
                      <th className="py-3 px-4">Token Symbol</th>
                      <th className="py-3 px-4">Underlying Stock</th>
                      <th className="py-3 px-4">Instrument ID</th>
                      <th className="py-3 px-4">Price (USDT)</th>
                      <th className="py-3 px-4">24h Change</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/60 font-mono">
                    {tokenizedEquities.map((tok) => {
                      const isPositive = (tok.change_24h_pct || 0) >= 0;
                      return (
                        <tr key={tok.symbol} className="hover:bg-gray-900/40 transition-colors">
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-gray-100 font-sans">{tok.symbol}</span>
                              <Badge variant="purple" size="sm">Tokenized</Badge>
                            </div>
                          </td>
                          <td className="py-3 px-4 font-sans text-gray-300">
                            {tok.underlying_symbol} ({tok.underlying_name})
                          </td>
                          <td className="py-3 px-4 text-gray-400 text-[11px]">{tok.provider_symbol}</td>
                          <td className="py-3 px-4 font-bold text-gray-100">
                            {tok.price ? `$${parseFloat(tok.price).toFixed(2)}` : (
                              <span className="text-gray-500 font-sans text-[11px]">Unavailable</span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            {tok.change_24h_pct !== null && tok.change_24h_pct !== undefined ? (
                              <span className={`flex items-center gap-1 font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                                {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                {isPositive ? `+${tok.change_24h_pct}%` : `${tok.change_24h_pct}%`}
                              </span>
                            ) : (
                              <span className="text-gray-500">—</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => openComparisonModal(tok.underlying_symbol)}
                              className="px-2.5 py-1 rounded bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 border border-purple-500/30 text-[11px] font-sans transition-colors inline-flex items-center gap-1"
                            >
                              <ArrowRightLeft className="h-3 w-3" /> Compare Reference
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-gray-500 font-mono">
                No active tokenized equity instruments currently discovered from OKX.
              </div>
            )}
          </Card>
        </div>
      )}

      {/* COMPARISON MODAL */}
      {comparisonModalSymbol && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <div className="flex items-center gap-2">
                <ArrowRightLeft className="h-5 w-5 text-blue-400" />
                <h3 className="text-base font-bold text-gray-100">
                  {comparisonModalSymbol} • Reference Price Comparison
                </h3>
              </div>
              <button
                onClick={() => setComparisonModalSymbol(null)}
                className="p-1 text-gray-400 hover:text-gray-200 rounded-lg hover:bg-gray-800 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {comparisonLoading ? (
              <div className="p-8 text-center text-xs text-gray-400 font-mono">
                Fetching comparison data...
              </div>
            ) : comparisonData ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {/* Traditional Equity Side */}
                  <div className="p-4 rounded-xl bg-gray-950/60 border border-gray-800 space-y-2">
                    <span className="text-[11px] text-gray-400 uppercase tracking-wider font-mono block">
                      Traditional Equity Reference
                    </span>
                    <div className="text-lg font-bold text-gray-100 font-mono">
                      {comparisonData.underlying_price ? `$${parseFloat(comparisonData.underlying_price).toFixed(2)}` : (
                        <span className="text-xs text-amber-400 font-sans font-normal">Unconfigured</span>
                      )}
                    </div>
                    <div className="text-[11px] text-gray-400 font-mono space-y-0.5">
                      <div>Symbol: <strong>{comparisonData.underlying_symbol}</strong></div>
                      <div>Source: <strong>{comparisonData.underlying_provider}</strong></div>
                      <div>State: <Badge variant={comparisonData.underlying_market_state === 'open' ? 'green' : 'gray'} size="sm">{comparisonData.underlying_market_state}</Badge></div>
                    </div>
                  </div>

                  {/* Tokenized Equity Side */}
                  <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-800/40 space-y-2">
                    <span className="text-[11px] text-purple-300 uppercase tracking-wider font-mono block">
                      OKX Tokenized Equity
                    </span>
                    <div className="text-lg font-bold text-purple-200 font-mono">
                      {comparisonData.tokenized_price ? `$${parseFloat(comparisonData.tokenized_price).toFixed(2)}` : (
                        <span className="text-xs text-gray-500 font-sans font-normal">Unavailable</span>
                      )}
                    </div>
                    <div className="text-[11px] text-purple-300 font-mono space-y-0.5">
                      <div>Symbol: <strong>{comparisonData.tokenized_symbol || 'None'}</strong></div>
                      <div>Venue: <strong>{comparisonData.tokenized_provider || 'OKX SPOT'}</strong></div>
                      <div>Type: <Badge variant="purple" size="sm">Tokenized</Badge></div>
                    </div>
                  </div>
                </div>

                {/* Price Difference Metrics */}
                {comparisonData.comparison_available ? (
                  <div className="p-4 rounded-xl bg-gray-950/80 border border-gray-800 flex items-center justify-between text-xs font-mono">
                    <span className="text-gray-300 font-medium">Reference Price Difference:</span>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-100">{comparisonData.price_difference_abs || '0.00'} USD</span>
                      <span className={`font-bold ${
                        (comparisonData.price_difference_pct || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        ({(comparisonData.price_difference_pct || 0) >= 0 ? '+' : ''}{comparisonData.price_difference_pct}%)
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-gray-950 border border-gray-800 text-xs text-gray-400 space-y-1">
                    <div className="font-semibold text-gray-300">Comparison Unavailable</div>
                    <div className="text-[11px] text-gray-400">{comparisonData.unavailability_reason}</div>
                  </div>
                )}

                {/* Compliance Disclaimer */}
                <div className="p-3 rounded-lg bg-gray-950 border border-gray-800/80 text-[11px] text-gray-400 flex items-start gap-2">
                  <Info className="h-4 w-4 text-blue-400 flex-shrink-0 mt-0.5" />
                  <span>{comparisonData.disclaimer}</span>
                </div>
              </div>
            ) : (
              <div className="p-4 text-center text-xs text-gray-500">Comparison data unavailable.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
