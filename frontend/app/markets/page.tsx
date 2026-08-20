'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { PriceChart } from '@/components/markets/PriceChart';
import {
  fetchMarketOverview,
  fetchAssetCandles,
  NormalizedTicker,
  NormalizedCandle,
} from '@/lib/api';
import { TrendingUp, TrendingDown, RefreshCw, BarChart2 } from 'lucide-react';

export default function MarketsPage() {
  const [tickers, setTickers] = useState<NormalizedTicker[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTC');
  const [timeframe, setTimeframe] = useState<string>('1H');
  const [candles, setCandles] = useState<NormalizedCandle[]>([]);
  const [loadingOverview, setLoadingOverview] = useState<boolean>(true);
  const [loadingCandles, setLoadingCandles] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadOverview = async () => {
    try {
      setError(null);
      const data = await fetchMarketOverview();
      setTickers(data.tickers);
    } catch (err: any) {
      console.error('Error loading market overview:', err);
      setError('Failed to connect to backend market service');
    } finally {
      setLoadingOverview(false);
    }
  };

  const loadCandles = async (symbol: string, tf: string) => {
    try {
      setLoadingCandles(true);
      const res = await fetchAssetCandles(symbol, tf, 100);
      setCandles(res.candles);
    } catch (err: any) {
      console.error(`Error loading candles for ${symbol}:`, err);
    } finally {
      setLoadingCandles(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      loadCandles(selectedSymbol, timeframe);
    }
  }, [selectedSymbol, timeframe]);

  const selectedTicker = tickers.find((t) => t.symbol === selectedSymbol);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-100">Live Market Explorer</h2>
          <p className="text-xs text-gray-400 mt-1">
            Real-time public ticker feeds and historical OHLCV candle charts (OKX Provider).
          </p>
        </div>
        <button
          onClick={loadOverview}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-800 bg-gray-900/60 text-xs text-gray-300 hover:bg-gray-800 transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loadingOverview ? 'animate-spin text-blue-400' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/40 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Asset Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {tickers.map((asset) => {
          const isSelected = asset.symbol === selectedSymbol;
          const isPositive = asset.change_24h_pct >= 0;
          return (
            <div
              key={asset.symbol}
              onClick={() => setSelectedSymbol(asset.symbol)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-blue-950/20 border-blue-500/50 shadow-lg'
                  : 'bg-[#121826] border-gray-800 hover:border-gray-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-gray-100">{asset.symbol}/USDT</span>
                  <Badge variant={isSelected ? 'blue' : 'gray'} size="sm">
                    {asset.name}
                  </Badge>
                </div>
                <span
                  className={`text-xs font-semibold flex items-center ${
                    isPositive ? 'text-emerald-400' : 'text-red-400'
                  }`}
                >
                  {isPositive ? <TrendingUp className="h-3 w-3 mr-0.5" /> : <TrendingDown className="h-3 w-3 mr-0.5" />}
                  {isPositive ? `+${asset.change_24h_pct}%` : `${asset.change_24h_pct}%`}
                </span>
              </div>

              <div className="text-xl font-bold font-mono text-gray-100 my-1">
                ${parseFloat(asset.price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>

              <div className="grid grid-cols-2 gap-2 mt-3 pt-2 border-t border-gray-800/60 text-[11px] font-mono text-gray-400">
                <div>
                  <span className="block text-[10px]">24h High:</span>
                  <span className="text-gray-200">${parseFloat(asset.high_24h).toLocaleString()}</span>
                </div>
                <div>
                  <span className="block text-[10px]">24h Low:</span>
                  <span className="text-gray-200">${parseFloat(asset.low_24h).toLocaleString()}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Asset Candle Chart Section */}
      <Card
        title={`${selectedSymbol}/USDT Historical Price Action`}
        subtitle="Normalized OHLCV candles retrieved from OKX public data stream"
        badge={<Badge variant="purple" size="sm">OKX DATA</Badge>}
        action={
          <div className="flex items-center gap-1.5 text-xs">
            {['15m', '1H', '4H', '1D'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 py-1 rounded font-mono text-xs transition-colors ${
                  timeframe === tf
                    ? 'bg-blue-600 text-white font-bold'
                    : 'bg-gray-900 text-gray-400 hover:text-gray-200'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        }
      >
        {loadingCandles ? (
          <div className="h-64 flex items-center justify-center text-xs text-gray-400 bg-gray-900/30 rounded-xl border border-gray-800">
            <RefreshCw className="h-5 w-5 animate-spin text-blue-400 mr-2" />
            <span>Loading normalized candle history...</span>
          </div>
        ) : (
          <PriceChart candles={candles} symbol={selectedSymbol} timeframe={timeframe} />
        )}

        <div className="mt-4 pt-3 border-t border-gray-800/60 flex items-center justify-between text-[11px] text-gray-400 font-mono">
          <span>Provider: <strong>OKX Public Market API</strong></span>
          <span>Max Candle Fetch: 300</span>
          <span>Zero Authentication Secrets Used</span>
        </div>
      </Card>
    </div>
  );
}
