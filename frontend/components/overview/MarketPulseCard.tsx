'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { fetchMarketOverview, NormalizedTicker } from '@/lib/api';
import { TrendingUp, TrendingDown, RefreshCw, AlertCircle } from 'lucide-react';

export const MarketPulseCard: React.FC = () => {
  const [tickers, setTickers] = useState<NormalizedTicker[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const loadMarketData = async () => {
    try {
      setError(null);
      const data = await fetchMarketOverview();
      setTickers(data.tickers);
      setLastUpdated(new Date(data.updated_at).toLocaleTimeString());
    } catch (err: any) {
      console.error('Error loading market pulse:', err);
      setError('Market data temporarily unavailable');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMarketData();
    // Auto-refresh polling every 20 seconds
    const interval = setInterval(loadMarketData, 20000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card
      title="Market Pulse"
      subtitle="Live market benchmarks & core crypto assets"
      badge={<Badge variant="green" size="sm">LIVE MARKET DATA</Badge>}
      action={
        <div className="flex items-center gap-2 text-xs text-gray-400">
          {lastUpdated && (
            <span className="text-[11px] font-mono">Updated {lastUpdated}</span>
          )}
          <button
            onClick={loadMarketData}
            className="p-1 hover:text-gray-200 transition-colors"
            title="Refresh Market Pulse"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      }
    >
      {error && (
        <div className="p-3 mb-3 rounded-lg bg-red-950/30 border border-red-800/40 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && tickers.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="p-3.5 rounded-lg bg-gray-900/40 border border-gray-800/60 animate-pulse space-y-2"
            >
              <div className="h-4 bg-gray-800 rounded w-1/3"></div>
              <div className="h-6 bg-gray-800 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {tickers.map((item) => {
            const isPositive = item.change_24h_pct >= 0;
            const priceFormatted = parseFloat(item.price).toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            });

            return (
              <div
                key={item.symbol}
                className="p-3.5 rounded-lg bg-gray-900/60 border border-gray-800/80 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-gray-200">{item.symbol}/USDT</span>
                  <span className="text-[10px] text-gray-400 font-mono">{item.name}</span>
                </div>

                <div className="flex items-baseline justify-between mt-2">
                  <span className="text-base font-bold text-gray-100 font-mono">${priceFormatted}</span>
                  <span
                    className={`text-xs font-semibold flex items-center ${
                      isPositive ? 'text-emerald-400' : 'text-red-400'
                    }`}
                  >
                    {isPositive ? (
                      <TrendingUp className="h-3 w-3 mr-0.5" />
                    ) : (
                      <TrendingDown className="h-3 w-3 mr-0.5" />
                    )}
                    {isPositive ? `+${item.change_24h_pct}%` : `${item.change_24h_pct}%`}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[10px] text-gray-400 mt-2 border-t border-gray-800/40 pt-1.5 font-mono">
                  <span>24h Vol: ${parseFloat(item.quote_volume_24h).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-3 pt-2 border-t border-gray-800/40 flex items-center justify-between text-[11px] text-gray-400 font-mono">
        <span>Market data provided by <strong>OKX Public API</strong></span>
        <span>Polling interval: 20s</span>
      </div>
    </Card>
  );
};
