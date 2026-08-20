'use client';

import React from 'react';
import { NormalizedCandle } from '@/lib/api';

interface PriceChartProps {
  candles: NormalizedCandle[];
  symbol: string;
  timeframe: string;
}

export const PriceChart: React.FC<PriceChartProps> = ({ candles, symbol, timeframe }) => {
  if (!candles || candles.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-gray-400 bg-gray-900/30 rounded-lg border border-gray-800">
        No candle data available
      </div>
    );
  }

  const prices = candles.map((c) => parseFloat(c.close));
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;

  const width = 700;
  const height = 240;
  const padding = 20;

  const points = candles.map((c, i) => {
    const x = padding + (i / (candles.length - 1)) * (width - 2 * padding);
    const y = height - padding - ((parseFloat(c.close) - minPrice) / priceRange) * (height - 2 * padding);
    return `${x},${y}`;
  }).join(' ');

  const isUp = prices[prices.length - 1] >= prices[0];
  const strokeColor = isUp ? '#10b981' : '#ef4444';
  const fillColor = isUp ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';

  const firstPoint = `${padding},${height - padding}`;
  const lastPoint = `${width - padding},${height - padding}`;
  const areaPoints = `${firstPoint} ${points} ${lastPoint}`;

  return (
    <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-gray-100">{symbol}/USDT Price Trend</span>
          <span className="text-xs text-gray-400 font-mono">({timeframe} Candles)</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="text-gray-400">Low: <strong className="text-gray-200">${minPrice.toLocaleString()}</strong></span>
          <span className="text-gray-400">High: <strong className="text-gray-200">${maxPrice.toLocaleString()}</strong></span>
        </div>
      </div>

      <div className="w-full overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56 text-xs">
          <defs>
            <linearGradient id={`gradient-${symbol}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeColor} stopOpacity="0.25" />
              <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Background Grid Lines */}
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#1f2937" strokeDasharray="3 3" />
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="#1f2937" strokeDasharray="3 3" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#1f2937" strokeDasharray="3 3" />

          {/* Area Fill */}
          <polygon points={areaPoints} fill={`url(#gradient-${symbol})`} />

          {/* Price Line */}
          <polyline
            fill="none"
            stroke={strokeColor}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />
        </svg>
      </div>

      <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono border-t border-gray-800/40 pt-2">
        <span>Start: {new Date(candles[0].timestamp).toLocaleDateString()}</span>
        <span>End: {new Date(candles[candles.length - 1].timestamp).toLocaleDateString()}</span>
      </div>
    </div>
  );
};
