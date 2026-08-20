'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { fetchPortfolioSummary, PortfolioSummary } from '@/lib/api';
import { PieChart, ArrowUpRight, ShieldCheck, Key, Wallet, ChevronRight } from 'lucide-react';
import Link from 'next/link';

export const PortfolioOverviewCard: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchPortfolioSummary()
      .then((data) => setPortfolio(data))
      .catch((err) => console.error('Error fetching overview portfolio:', err))
      .finally(() => setLoading(false));
  }, []);

  const isConfigured = portfolio?.data_status === 'configured';

  // Helper formatting routines
  const formatUsdtValue = (valStr: string | null, valuationAvailable: boolean) => {
    if (!valuationAvailable || !valStr) return 'N/A';
    const val = parseFloat(valStr);
    if (val === 0) return '$0.00';
    if (val < 0.01) return '<$0.01';
    return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatAllocPct = (pct: number) => {
    if (pct === 0) return '0.0%';
    if (pct < 0.01) return '<0.01%';
    return `${pct.toFixed(2)}%`;
  };

  const topHoldings = portfolio?.assets ? portfolio.assets.slice(0, 3) : [];
  const remainingAssetCount = portfolio ? Math.max(0, portfolio.asset_count - topHoldings.length) : 0;

  return (
    <Card
      title="Portfolio Overview"
      subtitle={isConfigured ? 'Live synchronized OKX read-only holdings' : 'OKX Read-Only Portfolio Integration'}
      badge={
        isConfigured ? (
          <Badge variant="green" size="sm">LIVE OKX PORTFOLIO</Badge>
        ) : (
          <Badge variant="amber" size="sm">UNCONFIGURED</Badge>
        )
      }
      action={
        <Link href="/portfolio" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium">
          View Portfolio <ArrowUpRight className="h-3 w-3" />
        </Link>
      }
    >
      {loading ? (
        <div className="p-4 rounded-lg bg-gray-900/40 border border-gray-800/60 animate-pulse h-28"></div>
      ) : isConfigured && portfolio ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Total Value Metric */}
            <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800/80 flex flex-col justify-between">
              <div>
                <p className="text-xs text-gray-400 font-medium">Total Estimated Portfolio</p>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-gray-100 font-mono">
                    ${parseFloat(portfolio.total_value_usdt).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-gray-800/60 flex items-center justify-between text-[11px]">
                <span className="text-emerald-400 flex items-center gap-1 font-mono font-medium">
                  <ShieldCheck className="h-3.5 w-3.5" /> {portfolio.asset_count} Active Assets Tracked
                </span>
                <span className="text-gray-500 font-mono text-[10px]">OKX Sync</span>
              </div>
            </div>

            {/* Asset Distribution */}
            <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800/80 md:col-span-2 space-y-2.5">
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-400 font-medium flex items-center gap-1.5">
                  <PieChart className="h-3.5 w-3.5 text-blue-400" /> Asset Distribution
                </p>
                <span className="text-[11px] text-gray-400 font-mono">
                  {portfolio.asset_count} Total Holdings
                </span>
              </div>

              {/* Allocation Progress Bar */}
              <div className="h-2.5 w-full bg-gray-800 rounded-full overflow-hidden flex gap-0.5 my-2">
                {portfolio.assets.slice(0, 4).map((asset, i) => {
                  const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-purple-500', 'bg-amber-500'];
                  return (
                    <div
                      key={asset.symbol}
                      className={`h-full ${colors[i % colors.length]}`}
                      style={{ width: `${Math.max(asset.allocation_pct, 0.5)}%` }}
                      title={`${asset.symbol}: ${asset.allocation_pct}%`}
                    ></div>
                  );
                })}
                {portfolio.assets.length > 4 && (
                  <div className="h-full bg-gray-600 flex-1" title="Other Assets / Dust"></div>
                )}
              </div>

              {/* Asset Allocation Legend */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono pt-1">
                {portfolio.assets.slice(0, 3).map((asset, i) => {
                  const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-purple-500'];
                  return (
                    <div key={asset.symbol} className="flex items-center gap-1.5">
                      <span className={`h-2 w-2 rounded-full ${colors[i % colors.length]}`}></span>
                      <span className="text-gray-200 font-medium">{asset.symbol}</span>
                      <span className="text-gray-400 font-mono ml-auto">{formatAllocPct(asset.allocation_pct)}</span>
                    </div>
                  );
                })}
                {remainingAssetCount > 0 && (
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-gray-500"></span>
                    <span className="text-gray-400 font-medium">+{remainingAssetCount} More</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Compact Top Holdings List */}
          <div className="p-3.5 rounded-lg bg-gray-900/40 border border-gray-800/60 space-y-2.5">
            <div className="flex items-center justify-between text-xs text-gray-400 font-medium">
              <span className="flex items-center gap-1.5">
                <Wallet className="h-3.5 w-3.5 text-emerald-400" /> Top Holdings
              </span>
              <span className="text-[11px] text-gray-500 font-mono">Sorted by Value</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {topHoldings.map((asset) => (
                <div
                  key={asset.symbol}
                  className="p-2.5 rounded bg-gray-900/80 border border-gray-800 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-gray-200 flex items-center gap-1">
                      <span>{asset.symbol}</span>
                      <span className="text-[10px] text-gray-400 font-mono font-normal">({asset.name})</span>
                    </div>
                    <div className="text-[10px] text-gray-400 font-mono mt-0.5">
                      {asset.total_balance} {asset.symbol}
                    </div>
                  </div>

                  <div className="text-right font-mono">
                    <div className="font-bold text-gray-100">
                      {formatUsdtValue(asset.estimated_value_usdt, asset.valuation_available)}
                    </div>
                    <div className="text-[10px] text-emerald-400">
                      {formatAllocPct(asset.allocation_pct)}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {remainingAssetCount > 0 && (
              <div className="flex items-center justify-between pt-1 border-t border-gray-800/40 text-[11px]">
                <span className="text-gray-400 font-mono">
                  +{remainingAssetCount} additional holdings ({portfolio.assets.slice(3).map(a => a.symbol).join(', ')})
                </span>
                <Link
                  href="/portfolio"
                  className="text-blue-400 hover:text-blue-300 font-medium flex items-center gap-0.5"
                >
                  View all {portfolio.asset_count} assets <ChevronRight className="h-3 w-3" />
                </Link>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <Key className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-200">Connect OKX Read-Only Account</h4>
              <p className="text-[11px] text-gray-400">Configure read-only API credentials in backend environment to view your live portfolio.</p>
            </div>
          </div>
          <Link
            href="/portfolio"
            className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
          >
            Setup
          </Link>
        </div>
      )}
    </Card>
  );
};
