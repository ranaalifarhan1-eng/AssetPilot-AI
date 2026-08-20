'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { fetchPortfolioSummary, PortfolioSummary } from '@/lib/api';
import { TrendingUp, PieChart, ArrowUpRight, ShieldCheck, Key } from 'lucide-react';
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
        <Link href="/portfolio" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
          Manage <ArrowUpRight className="h-3 w-3" />
        </Link>
      }
    >
      {loading ? (
        <div className="p-4 rounded-lg bg-gray-900/40 border border-gray-800/60 animate-pulse h-24"></div>
      ) : isConfigured && portfolio ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Total Value Metric */}
          <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800/80">
            <p className="text-xs text-gray-400 font-medium">Total Estimated Portfolio</p>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-gray-100 font-mono">
                ${parseFloat(portfolio.total_value_usdt).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <p className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1 font-mono">
              <ShieldCheck className="h-3 w-3" /> {portfolio.asset_count} Active Assets Tracked
            </p>
          </div>

          {/* Allocation Breakdown */}
          <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800/80 md:col-span-2">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-gray-400 font-medium flex items-center gap-1.5">
                <PieChart className="h-3.5 w-3.5 text-blue-400" /> Asset Distribution
              </p>
              <span className="text-[11px] text-gray-400 font-mono">
                OKX Read-Only Sync
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
                    style={{ width: `${asset.allocation_pct}%` }}
                    title={`${asset.symbol}: ${asset.allocation_pct}%`}
                  ></div>
                );
              })}
            </div>

            {/* Asset Allocation Legend */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 text-xs font-mono">
              {portfolio.assets.slice(0, 4).map((asset, i) => {
                const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-purple-500', 'bg-amber-500'];
                return (
                  <div key={asset.symbol} className="flex items-center gap-1.5">
                    <span className={`h-2 w-2 rounded-full ${colors[i % colors.length]}`}></span>
                    <span className="text-gray-300 font-medium">{asset.symbol}</span>
                    <span className="text-gray-400 font-mono ml-auto">{asset.allocation_pct}%</span>
                  </div>
                );
              })}
            </div>
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
