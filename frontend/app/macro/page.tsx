'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';
import {
  EconomicEvent,
  YieldCurveData,
  MacroStatusResponse,
  fetchMacroStatus,
  fetchUpcomingMacro,
  fetchRecentMacro,
  fetchTreasuryYieldCurve,
} from '@/lib/api';
import {
  Globe,
  Calendar,
  Clock,
  TrendingUp,
  AlertCircle,
  ShieldCheck,
  RefreshCw,
  Landmark,
  Layers,
  ArrowUpRight,
  Sparkles,
  DollarSign,
  Activity,
  CheckCircle,
  ExternalLink,
} from 'lucide-react';

export default function MacroPage() {
  const [status, setStatus] = useState<MacroStatusResponse | null>(null);
  const [upcoming, setUpcoming] = useState<EconomicEvent[]>([]);
  const [recent, setRecent] = useState<EconomicEvent[]>([]);
  const [yieldCurve, setYieldCurve] = useState<YieldCurveData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active Tab: 'upcoming' | 'recent' | 'yield-curve'
  const [activeTab, setActiveTab] = useState<'upcoming' | 'recent' | 'yield-curve'>('upcoming');

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [highImpactOnly, setHighImpactOnly] = useState<boolean>(false);
  const [portfolioOnly, setPortfolioOnly] = useState<boolean>(false);

  const loadMacroData = async () => {
    try {
      setError(null);
      const [statusRes, upRes, recRes, curveRes] = await Promise.all([
        fetchMacroStatus(),
        fetchUpcomingMacro('30d', 50),
        fetchRecentMacro(30),
        fetchTreasuryYieldCurve(),
      ]);
      setStatus(statusRes);
      setUpcoming(upRes);
      setRecent(recRes);
      setYieldCurve(curveRes);
    } catch (err: any) {
      console.error('Error loading macro data:', err);
      setError('Failed to fetch macroeconomic intelligence data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadMacroData();
    const interval = setInterval(loadMacroData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadMacroData();
  };

  const formatTime = (utcStr: string) => {
    try {
      const d = new Date(utcStr);
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short',
      });
    } catch {
      return utcStr;
    }
  };

  const formatRelativeTime = (utcStr: string) => {
    try {
      const d = new Date(utcStr);
      const now = new Date();
      const diffMs = d.getTime() - now.getTime();
      const diffHrs = Math.round(diffMs / (1000 * 60 * 60));
      const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

      if (diffMs > 0) {
        if (diffHrs < 24) return `In ${Math.max(1, diffHrs)}h`;
        return `In ${diffDays}d`;
      } else {
        const absHrs = Math.abs(diffHrs);
        const absDays = Math.abs(diffDays);
        if (absHrs < 24) return `${Math.max(1, absHrs)}h ago`;
        return `${absDays}d ago`;
      }
    } catch {
      return '';
    }
  };

  const filterList = (events: EconomicEvent[]) => {
    return events.filter((e) => {
      if (selectedCategory !== 'All' && e.category.toLowerCase() !== selectedCategory.toLowerCase()) {
        return false;
      }
      if (highImpactOnly && e.importance !== 'high') {
        return false;
      }
      if (portfolioOnly && e.portfolio_exposure.length === 0) {
        return false;
      }
      return true;
    });
  };

  const filteredUpcoming = useMemo(() => filterList(upcoming), [upcoming, selectedCategory, highImpactOnly, portfolioOnly]);
  const filteredRecent = useMemo(() => filterList(recent), [recent, selectedCategory, highImpactOnly, portfolioOnly]);

  const nextHighImpact = upcoming.find((e) => e.importance === 'high');
  const highImpactThisWeek = upcoming.filter((e) => {
    if (e.importance !== 'high') return false;
    const d = new Date(e.scheduled_at);
    const in7Days = new Date();
    in7Days.setDate(in7Days.getDate() + 7);
    return d <= in7Days;
  }).length;
  const latestRelease = recent[0];

  const categories = ['All', 'Monetary Policy', 'Inflation', 'Labor', 'Growth', 'Liquidity / Rates'];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <Globe className="h-5 w-5 text-blue-400" /> Macro & Economic Intelligence
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            Authoritative U.S. macroeconomic releases, Federal Reserve monetary calendars, and sovereign yield curves.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/20 px-3 py-1.5 rounded-lg border border-emerald-800/40 font-medium">
            <ShieldCheck className="h-4 w-4" />
            <span>Authoritative Sources Active</span>
          </div>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-medium transition-colors border border-gray-700 disabled:opacity-50"
            title="Refresh Macro Data"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin text-blue-400' : ''}`} />
            <span>{refreshing ? 'Syncing...' : 'Sync'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/40 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Next High Impact */}
        <Card title="Next High-Impact Event">
          <div className="mt-1 space-y-1">
            <div className="text-sm font-bold text-gray-100 line-clamp-1">
              {nextHighImpact ? nextHighImpact.indicator_name || nextHighImpact.event_name : 'No scheduled events'}
            </div>
            <div className="text-xs text-blue-400 font-mono font-medium flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{nextHighImpact ? `${formatTime(nextHighImpact.scheduled_at)} (${formatRelativeTime(nextHighImpact.scheduled_at)})` : 'N/A'}</span>
            </div>
            {nextHighImpact && (
              <div className="text-[10px] text-gray-400 font-mono">
                {nextHighImpact.category} {nextHighImpact.previous !== null ? `| Prior: ${nextHighImpact.previous}${nextHighImpact.unit}` : ''}
              </div>
            )}
          </div>
        </Card>

        {/* High Impact 7d Count */}
        <Card title="High Impact (Next 7 Days)">
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-gray-100 font-mono">{highImpactThisWeek}</span>
            <span className="text-xs text-gray-400">Events Scheduled</span>
          </div>
          <p className="text-[11px] text-emerald-400 mt-1">BEA, BLS, FOMC & Key Releases</p>
        </Card>

        {/* Latest Macro Release */}
        <Card title="Latest Macro Release">
          <div className="mt-1 space-y-1">
            <div className="text-sm font-bold text-gray-100 line-clamp-1">
              {latestRelease ? latestRelease.indicator_name || latestRelease.event_name : 'N/A'}
            </div>
            {latestRelease && latestRelease.actual !== null ? (
              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="text-gray-200 font-bold">Act: {latestRelease.actual}{latestRelease.unit}</span>
                {latestRelease.forecast !== null ? (
                  <span className="text-gray-400">Est: {latestRelease.forecast}{latestRelease.unit}</span>
                ) : (
                  <span className="text-gray-500 text-[10px]">Est: —</span>
                )}
                {latestRelease.surprise_absolute !== null && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${latestRelease.surprise_absolute > 0 ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'}`}>
                    {latestRelease.surprise_absolute > 0 ? `+${latestRelease.surprise_absolute}` : latestRelease.surprise_absolute}
                  </span>
                )}
              </div>
            ) : (
              <div className="text-xs text-gray-400 font-mono">Awaiting updates</div>
            )}
            <div className="text-[10px] text-gray-500 font-mono">
              {latestRelease ? formatTime(latestRelease.scheduled_at) : ''}
            </div>
          </div>
        </Card>

        {/* Yield Curve Spread */}
        <Card title="U.S. 10Y Yield & Curve Spread">
          <div className="mt-1 space-y-1">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-gray-100 font-mono">
                {yieldCurve?.rates['10Y'] ? `${yieldCurve.rates['10Y'].toFixed(2)}%` : 'N/A'}
              </span>
              <span className="text-xs text-gray-400 font-mono">10Y Benchmark</span>
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-gray-400">10Y-2Y Spread:</span>
              <span className={`font-bold ${yieldCurve?.curve_inversion ? 'text-red-400' : 'text-emerald-400'}`}>
                {yieldCurve ? `${yieldCurve.spread_10y_2y_bps > 0 ? '+' : ''}${yieldCurve.spread_10y_2y_bps.toFixed(1)} bps` : 'N/A'}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('upcoming')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              activeTab === 'upcoming'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
            }`}
          >
            <Calendar className="h-3.5 w-3.5" /> Upcoming Calendar ({upcoming.length})
          </button>

          <button
            onClick={() => setActiveTab('recent')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              activeTab === 'recent'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
            }`}
          >
            <CheckCircle className="h-3.5 w-3.5" /> Recent Releases ({recent.length})
          </button>

          <button
            onClick={() => setActiveTab('yield-curve')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              activeTab === 'yield-curve'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
            }`}
          >
            <TrendingUp className="h-3.5 w-3.5" /> Treasury Yield Curve
          </button>
        </div>

        {/* Category & Filters Bar */}
        {activeTab !== 'yield-curve' && (
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1 bg-gray-900/80 p-1 rounded-lg border border-gray-800 text-[11px]">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded font-medium transition-colors ${
                    selectedCategory === cat
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <button
              onClick={() => setHighImpactOnly(!highImpactOnly)}
              className={`px-2.5 py-1.5 rounded-lg text-[11px] font-semibold transition-colors border ${
                highImpactOnly
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'text-gray-400 border-gray-800 hover:bg-gray-800'
              }`}
            >
              High Impact Only
            </button>

            <button
              onClick={() => setPortfolioOnly(!portfolioOnly)}
              className={`px-2.5 py-1.5 rounded-lg text-[11px] font-semibold transition-colors border ${
                portfolioOnly
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  : 'text-gray-400 border-gray-800 hover:bg-gray-800'
              }`}
            >
              Portfolio Relevant
            </button>
          </div>
        )}
      </div>

      {/* Tab 1: Upcoming Economic Calendar */}
      {activeTab === 'upcoming' && (
        <Card
          title="Scheduled Macroeconomic Events"
          subtitle="Timezone-aware release dates directly from official agency calendars"
          badge={<Badge variant="blue" size="sm">OFFICIAL SCHEDULE</Badge>}
        >
          {loading ? (
            <div className="p-8 text-center text-xs text-gray-400 animate-pulse">Loading upcoming calendar...</div>
          ) : filteredUpcoming.length === 0 ? (
            <div className="p-8 text-center text-xs text-gray-400 font-mono">
              No upcoming macro events match the selected filters.
            </div>
          ) : (
            <div className="divide-y divide-gray-800/60">
              {filteredUpcoming.map((event) => (
                <div key={event.id} className="py-4 hover:bg-gray-900/30 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Left: Timing & Event Info */}
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold font-mono uppercase ${
                        event.importance === 'high'
                          ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                          : event.importance === 'medium'
                          ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                          : 'bg-gray-700/30 text-gray-400 border border-gray-700/50'
                      }`}>
                        {event.importance}
                      </span>
                      <span className="text-[10px] text-gray-400 font-mono bg-gray-800 px-2 py-0.5 rounded">
                        {event.category}
                      </span>
                      <span className="text-xs text-blue-400 font-mono font-medium flex items-center gap-1">
                        <Clock className="h-3 w-3" /> {formatTime(event.scheduled_at)}
                      </span>
                      <span className="text-[10px] text-emerald-400 font-mono font-bold">
                        ({formatRelativeTime(event.scheduled_at)})
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-gray-100 flex items-center gap-2">
                        <span>{event.indicator_name || event.event_name}</span>
                        {event.period && (
                          <span className="text-xs text-gray-400 font-normal font-mono">({event.period})</span>
                        )}
                      </h4>
                      {event.release_name && event.release_name !== (event.indicator_name || event.event_name) && (
                        <div className="text-[11px] text-gray-500 font-mono">
                          Publication: {event.release_name}
                        </div>
                      )}
                    </div>

                    {event.market_impact_summary && (
                      <p className="text-xs text-gray-400 max-w-3xl leading-relaxed">
                        {event.market_impact_summary}
                      </p>
                    )}

                    {/* Related Assets & Portfolio Exposure */}
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      {event.portfolio_exposure.length > 0 && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono font-bold flex items-center gap-1">
                          <ShieldCheck className="h-3 w-3" /> Portfolio Exposure: {event.portfolio_exposure.join(', ')}
                        </span>
                      )}
                      {event.related_assets.map((asset) => (
                        <span key={asset} className="text-[10px] px-1.5 py-0.2 rounded bg-gray-800/80 text-gray-300 font-mono">
                          {asset}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Right: Forecast vs Previous Figures & Provenance */}
                  <div className="flex items-center gap-6 text-right font-mono flex-shrink-0">
                    <div className="space-y-0.5">
                      <div className="text-[10px] text-gray-500 uppercase">Consensus Est.</div>
                      <div className="text-sm font-bold text-gray-200">
                        {event.forecast !== null ? `${event.forecast}${event.unit}` : '—'}
                      </div>
                      {event.forecast === null && (
                        <div className="text-[9px] text-gray-500">Not available</div>
                      )}
                    </div>

                    <div className="space-y-0.5">
                      <div className="text-[10px] text-gray-500 uppercase">Previous</div>
                      <div className="text-sm font-bold text-gray-400">
                        {event.previous !== null ? `${event.previous}${event.unit}` : '—'}
                      </div>
                    </div>

                    {event.source_url && (
                      <a
                        href={event.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2 text-gray-500 hover:text-blue-400 transition-colors"
                        title={`Source: ${event.source}`}
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Tab 2: Recent Releases & Surprises */}
      {activeTab === 'recent' && (
        <Card
          title="Recent Macroeconomic Releases"
          subtitle="Official published results with economic context and source provenance"
          badge={<Badge variant="green" size="sm">PUBLISHED DATA</Badge>}
        >
          {loading ? (
            <div className="p-8 text-center text-xs text-gray-400 animate-pulse">Loading recent releases...</div>
          ) : filteredRecent.length === 0 ? (
            <div className="p-8 text-center text-xs text-gray-400 font-mono">
              No recent macro releases match the selected filters.
            </div>
          ) : (
            <div className="divide-y divide-gray-800/60">
              {filteredRecent.map((event) => (
                <div key={event.id} className="py-4 hover:bg-gray-900/30 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Left Info */}
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-gray-400 font-mono bg-gray-800 px-2 py-0.5 rounded">
                        {event.category}
                      </span>
                      <span className="text-xs text-gray-400 font-mono">
                        Released: {formatTime(event.scheduled_at)} ({formatRelativeTime(event.scheduled_at)})
                      </span>
                      <span className="text-[10px] text-gray-500 font-mono">
                        Source: {event.source}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-gray-100 flex items-center gap-2">
                        <span>{event.indicator_name || event.event_name}</span>
                        {event.period && (
                          <span className="text-xs text-gray-400 font-normal font-mono">({event.period})</span>
                        )}
                      </h4>
                      {event.release_name && event.release_name !== (event.indicator_name || event.event_name) && (
                        <div className="text-[11px] text-gray-500 font-mono">
                          Publication: {event.release_name}
                        </div>
                      )}
                    </div>

                    {/* Context & Interpretation */}
                    {event.interpretation_direction && (
                      <div className="text-xs text-blue-300 bg-blue-950/30 border border-blue-800/40 p-2 rounded-lg max-w-2xl leading-relaxed">
                        <span className="font-semibold">{event.interpretation_direction}: </span>
                        <span>{event.market_impact_summary}</span>
                      </div>
                    )}

                    {/* Portfolio Exposure */}
                    {event.portfolio_exposure.length > 0 && (
                      <div className="pt-1">
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono font-bold flex items-center gap-1 inline-flex">
                          <ShieldCheck className="h-3 w-3" /> Portfolio Exposure: {event.portfolio_exposure.join(', ')}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Right Metrics: Actual, Forecast, Previous, Surprise */}
                  <div className="flex items-center gap-5 text-right font-mono flex-shrink-0">
                    <div className="space-y-0.5">
                      <div className="text-[10px] text-gray-500 uppercase">Actual</div>
                      <div className="text-base font-bold text-gray-100">
                        {event.actual !== null ? `${event.actual}${event.unit}` : '—'}
                      </div>
                    </div>

                    <div className="space-y-0.5">
                      <div className="text-[10px] text-gray-500 uppercase">Forecast</div>
                      <div className="text-xs text-gray-400">
                        {event.forecast !== null ? `${event.forecast}${event.unit}` : '—'}
                      </div>
                    </div>

                    <div className="space-y-0.5">
                      <div className="text-[10px] text-gray-500 uppercase">Previous</div>
                      <div className="text-xs text-gray-500">
                        {event.previous !== null ? `${event.previous}${event.unit}` : '—'}
                      </div>
                    </div>

                    {event.surprise_absolute !== null ? (
                      <div className="space-y-0.5 min-w-[70px]">
                        <div className="text-[10px] text-gray-500 uppercase">Surprise</div>
                        <div className={`text-xs font-bold ${
                          event.surprise_absolute > 0
                            ? 'text-amber-400'
                            : event.surprise_absolute < 0
                            ? 'text-blue-400'
                            : 'text-gray-400'
                        }`}>
                          {event.surprise_absolute > 0 ? `+${event.surprise_absolute}` : event.surprise_absolute}
                          {event.surprise_percentage !== null ? ` (${event.surprise_percentage > 0 ? '+' : ''}${event.surprise_percentage}%)` : ''}
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-0.5 min-w-[70px]">
                        <div className="text-[10px] text-gray-500 uppercase">Surprise</div>
                        <div className="text-xs text-gray-500">—</div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Tab 3: U.S. Treasury Yield Curve */}
      {activeTab === 'yield-curve' && (
        <div className="space-y-4">
          <Card
            title="U.S. Department of the Treasury Daily Yield Curve"
            subtitle={`Official benchmark sovereign interest rates as of ${yieldCurve?.date || 'latest available date'}`}
            badge={<Badge variant="blue" size="sm">TREASURY DATA</Badge>}
          >
            {yieldCurve ? (
              <div className="space-y-6">
                {/* Curve Status Alert */}
                <div className={`p-4 rounded-xl border flex items-start gap-3 text-xs ${
                  yieldCurve.curve_inversion
                    ? 'bg-red-950/30 border-red-800/40 text-red-300'
                    : 'bg-emerald-950/20 border-emerald-800/40 text-emerald-300'
                }`}>
                  <Activity className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <span className="font-bold">
                      {yieldCurve.curve_inversion ? 'Yield Curve Inversion Active' : 'Normal Upward Sloping Yield Curve'}
                    </span>
                    <p className="text-gray-300 leading-relaxed">
                      10-Year yield ({yieldCurve.rates['10Y']}%) vs 2-Year yield ({yieldCurve.rates['2Y']}%) spread is <strong>{yieldCurve.spread_10y_2y_bps > 0 ? '+' : ''}{yieldCurve.spread_10y_2y_bps} bps</strong>.
                      {yieldCurve.curve_inversion
                        ? ' Short-term sovereign yields exceed long-term yields, which has historically preceded economic contractions.'
                        : ' Long-term yields exceed short-term yields, indicating standard duration risk compensation.'}
                    </p>
                  </div>
                </div>

                {/* Tenors Rates Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
                  {Object.entries(yieldCurve.rates).map(([tenor, rate]) => (
                    <div key={tenor} className="p-3 rounded-lg bg-gray-900/80 border border-gray-800 font-mono text-center">
                      <div className="text-xs text-gray-400 uppercase font-semibold">{tenor}</div>
                      <div className="text-lg font-bold text-gray-100 mt-1">{rate.toFixed(2)}%</div>
                    </div>
                  ))}
                </div>

                {/* Explanatory notes */}
                <div className="text-[11px] text-gray-500 font-mono border-t border-gray-800 pt-3 flex items-center justify-between">
                  <span>Source: {yieldCurve.source} (Daily Treasury Par Yield Curve)</span>
                  <span>Observation Date: {yieldCurve.date}</span>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-gray-400 font-mono">
                Treasury Yield Curve data currently loading or unavailable.
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
