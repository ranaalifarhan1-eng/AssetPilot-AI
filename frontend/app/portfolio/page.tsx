'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { fetchPortfolioSummary, fetchPortfolioStatus, PortfolioSummary, PortfolioStatusResponse } from '@/lib/api';
import { ShieldCheck, RefreshCw, AlertCircle, Key, Lock, ArrowUpRight, Layers, AlertTriangle, Clock, Info } from 'lucide-react';

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
            Secure, non-custodial read-only synchronization across OKX Trading, Funding & Earn balances.
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

      {/* Partial Valuation Alert Banner */}
      {isConfigured && portfolio && portfolio.valuation_status === 'partial' && (
        <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/50 text-xs text-amber-300 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-amber-200">Partial Valuation Active</div>
            <p className="text-gray-300 leading-relaxed">
              Price lookups for <strong>{portfolio.unvalued_asset_count} asset(s)</strong> ({portfolio.unvalued_assets.join(', ')}) are currently unavailable from live market feeds. 
              The total equity displayed below (<strong>${parseFloat(portfolio.known_value_usdt).toFixed(2)} USDT</strong>) represents known valued assets only and is not a complete valuation.
            </p>
          </div>
        </div>
      )}

      {/* Stale Complete Valuation Banner */}
      {isConfigured && portfolio && portfolio.valuation_status === 'stale_complete' && (
        <div className="p-3.5 rounded-xl bg-blue-950/30 border border-blue-800/50 text-xs text-blue-300 flex items-start gap-3">
          <Clock className="h-4 w-4 text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-blue-200">Stale Complete Valuation Preserved: </span>
            <span className="text-gray-300">
              Retaining last complete valuation (${parseFloat(portfolio.total_value_usdt).toFixed(2)} USDT) while awaiting live price updates for: {portfolio.unvalued_assets.join(', ')}.
            </span>
          </div>
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
            <Card title={portfolio.valuation_status === 'partial' ? "Known Portfolio Equity (Partial)" : "Connected Account Value"}>
              <div className="mt-1">
                <span className="text-2xl font-bold text-gray-100 font-mono">
                  ${parseFloat(portfolio.valuation_status === 'partial' ? portfolio.known_value_usdt : portfolio.total_value_usdt).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="text-xs text-gray-400 block mt-1">
                  {portfolio.valuation_status === 'partial' ? 'USDT (Partial — Awaiting Unpriced Assets)' : 'USDT Equivalent'}
                </span>
              </div>
            </Card>

            <Card title="Tracked Holdings">
              <div className="mt-1">
                <span className="text-2xl font-bold text-gray-100 font-mono">
                  {portfolio.asset_count}
                </span>
                <span className="text-xs text-gray-400 block mt-1">Trading, Funding & Earn Balances</span>
              </div>
            </Card>

            <Card title="Valuation Status">
              <div className="mt-1 flex items-baseline gap-2">
                {portfolio.valuation_status === 'complete' ? (
                  <span className="text-base font-bold text-emerald-400 font-mono flex items-center gap-1">
                    <ShieldCheck className="h-4 w-4" /> 100% Live Valued
                  </span>
                ) : portfolio.valuation_status === 'stale_complete' ? (
                  <span className="text-base font-bold text-amber-400 font-mono flex items-center gap-1">
                    <Clock className="h-4 w-4" /> Stale Valuation
                  </span>
                ) : (
                  <span className="text-base font-bold text-amber-400 font-mono flex items-center gap-1">
                    <AlertTriangle className="h-4 w-4" /> Partial ({portfolio.valued_asset_count}/{portfolio.asset_count} Valued)
                  </span>
                )}
              </div>
              <span className="text-xs text-gray-500 block mt-1 font-mono">
                Last synced: {portfolio.last_synced_at ? new Date(portfolio.last_synced_at).toLocaleTimeString() : 'N/A'}
              </span>
            </Card>
          </div>

          {/* Holdings & Accounts Table */}
          <Card
            title="Portfolio Holdings & Account Breakdown"
            subtitle="Aggregated across OKX Trading, Funding & Earn accounts"
            badge={
              portfolio.valuation_status === 'complete' ? (
                <Badge variant="green" size="sm">LIVE VALUATION</Badge>
              ) : (
                <Badge variant="amber" size="sm">{portfolio.valuation_status.toUpperCase()}</Badge>
              )
            }
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
                      <td className="py-3 px-4">
                        {asset.price_usdt ? (
                          <span>${parseFloat(asset.price_usdt) >= 1 ? parseFloat(asset.price_usdt).toFixed(2) : parseFloat(asset.price_usdt).toFixed(4)}</span>
                        ) : (
                          <span className="text-gray-500 text-[11px] font-sans">N/A</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-bold text-gray-100">
                        {asset.valuation_available && asset.estimated_value_usdt ? (
                          `$${parseFloat(asset.estimated_value_usdt).toFixed(2)}`
                        ) : (
                          <span className="text-gray-500 text-[11px] font-sans font-normal">Unpriced</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {asset.valuation_available && asset.allocation_pct > 0 ? (
                          <span className="text-emerald-400 font-semibold">{asset.allocation_pct.toFixed(2)}%</span>
                        ) : (
                          <span className="text-gray-500 text-[11px] font-sans">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
