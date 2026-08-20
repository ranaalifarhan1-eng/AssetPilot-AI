'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { fetchPortfolioSummary, fetchPortfolioStatus, PortfolioSummary, PortfolioStatusResponse } from '@/lib/api';
import { ShieldCheck, RefreshCw, AlertCircle, Key, Lock, ArrowUpRight, Layers } from 'lucide-react';

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [status, setStatus] = useState<PortfolioStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [summaryRes, statusRes] = await Promise.all([
        fetchPortfolioSummary(),
        fetchPortfolioStatus(),
      ]);
      setPortfolio(summaryRes);
      setStatus(statusRes);
    } catch (err: any) {
      console.error('Error loading portfolio:', err);
      setError('Failed to connect to backend portfolio service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // 30s refresh
    return () => clearInterval(interval);
  }, []);

  const isConfigured = portfolio?.data_status === 'configured';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-100">Personal Portfolio</h2>
          <p className="text-xs text-gray-400 mt-1">
            Secure, non-custodial read-only synchronization across OKX Trading & Funding balances.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/20 px-3 py-1.5 rounded-lg border border-emerald-800/40 font-medium">
            <ShieldCheck className="h-4 w-4" />
            <span>OKX Read-Only Mode</span>
          </div>

          <button
            onClick={loadData}
            className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 rounded-lg transition-colors"
            title="Sync Portfolio"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/40 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Unconfigured State Banner */}
      {!loading && !isConfigured && (
        <Card
          title="Connect OKX Read-Only Account"
          subtitle="View your actual OKX account balances safely without trade execution or withdrawal access."
          badge={<Badge variant="amber">SETUP REQUIRED</Badge>}
        >
          <div className="p-6 rounded-xl bg-gray-900/60 border border-gray-800 space-y-4">
            <div className="flex items-start gap-4">
              <div className="h-10 w-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 flex-shrink-0">
                <Key className="h-5 w-5" />
              </div>
              <div className="space-y-2 text-xs text-gray-300 leading-relaxed">
                <h4 className="text-sm font-semibold text-gray-100">Setup Instructions:</h4>
                <ol className="list-decimal list-inside space-y-1.5 text-gray-300">
                  <li>Log in to your <strong>OKX Account</strong> and navigate to API Management.</li>
                  <li>Create a new API Key with <strong className="text-emerald-400">Read Permission ONLY</strong>.</li>
                  <li><strong className="text-red-400">DO NOT</strong> enable Trade or Withdraw permissions.</li>
                  <li>Add your credentials to your local backend environment file (<code className="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300">backend/.env</code>):</li>
                </ol>
                <div className="p-3 rounded bg-gray-950 font-mono text-[11px] text-gray-300 border border-gray-800 space-y-1">
                  <div>OKX_API_KEY=your_read_only_api_key</div>
                  <div>OKX_API_SECRET=your_api_secret</div>
                  <div>OKX_API_PASSPHRASE=your_passphrase</div>
                </div>
                <p className="text-[11px] text-gray-400 pt-1">
                  Restart the backend service after updating <code className="text-gray-300">.env</code>. Credentials remain strictly isolated on your local server.
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Configured State Portfolio View */}
      {isConfigured && portfolio && (
        <>
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card title="Total Estimated Equity">
              <div className="mt-1">
                <span className="text-2xl font-bold text-gray-100 font-mono">
                  ${parseFloat(portfolio.total_value_usdt).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
                <span className="text-xs text-gray-400 block mt-1">USDT Equivalent</span>
              </div>
            </Card>

            <Card title="Tracked Assets">
              <div className="mt-1">
                <span className="text-2xl font-bold text-gray-100 font-mono">
                  {portfolio.asset_count}
                </span>
                <span className="text-xs text-gray-400 block mt-1">Trading & Funding Balances</span>
              </div>
            </Card>

            <Card title="Last Synchronized">
              <div className="mt-1">
                <span className="text-base font-bold text-gray-100 font-mono">
                  {portfolio.last_synced_at ? new Date(portfolio.last_synced_at).toLocaleTimeString() : 'N/A'}
                </span>
                <span className="text-xs text-emerald-400 block mt-1 flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" /> OKX API Connected
                </span>
              </div>
            </Card>
          </div>

          {/* Holdings & Accounts Table */}
          <Card
            title="Portfolio Holdings & Account Breakdown"
            subtitle="Aggregated across OKX Trading & Funding accounts"
            badge={<Badge variant="blue" size="sm">LIVE OKX DATA</Badge>}
          >
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-900/80 text-gray-400 font-mono uppercase text-[10px] border-b border-gray-800">
                  <tr>
                    <th className="py-3 px-4">Asset</th>
                    <th className="py-3 px-4">Total Balance</th>
                    <th className="py-3 px-4">Location Breakdown</th>
                    <th className="py-3 px-4">Price (USDT)</th>
                    <th className="py-3 px-4">Est. Value (USDT)</th>
                    <th className="py-3 px-4">Allocation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60 font-mono">
                  {portfolio.assets.map((asset) => (
                    <tr key={asset.symbol} className="hover:bg-gray-900/40 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2 font-sans font-bold text-gray-100">
                          <span>{asset.symbol}</span>
                          <span className="text-[10px] font-normal text-gray-400 font-mono">({asset.name})</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-bold text-gray-200">{asset.total_balance}</td>
                      <td className="py-3 px-4">
                        <div className="space-y-0.5">
                          {asset.account_sources.map((src, i) => (
                            <div key={i} className="text-[11px] flex items-center gap-1">
                              <span className="text-gray-400">{src.source}:</span>
                              <span className="text-gray-200">{src.balance}</span>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-gray-300">
                        {asset.price_usdt ? `$${parseFloat(asset.price_usdt).toLocaleString()}` : 'N/A'}
                      </td>
                      <td className="py-3 px-4 font-bold text-gray-100">
                        {asset.estimated_value_usdt ? `$${parseFloat(asset.estimated_value_usdt).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-blue-500 h-full rounded-full"
                              style={{ width: `${Math.min(asset.allocation_pct, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-gray-300">{asset.allocation_pct}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {/* Security Statement Footer */}
      <div className="p-4 rounded-xl bg-gray-900/40 border border-gray-800/80 flex items-center justify-between text-[11px] text-gray-400 font-mono">
        <span className="flex items-center gap-1.5">
          <Lock className="h-3.5 w-3.5 text-emerald-400" /> Strictly Read-Only API Integration
        </span>
        <span>No Trading or Withdrawal Permissions</span>
      </div>
    </div>
  );
}
