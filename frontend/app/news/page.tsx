'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';
import {
  fetchNewsFeed,
  fetchNewsStatus,
  NewsArticle,
  NewsStatusResponse,
} from '@/lib/api';
import {
  Newspaper,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Flame,
  Search,
  Filter,
  CheckCircle2,
  Building2,
  Clock
} from 'lucide-react';

function timeAgo(dateString: string): string {
  try {
    const pub = new Date(dateString);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - pub.getTime()) / 1000);
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    const diffDays = Math.floor(diffHrs / 24);
    return `${diffDays}d ago`;
  } catch {
    return 'Recently';
  }
}

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [statusInfo, setStatusInfo] = useState<NewsStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [selectedTab, setSelectedTab] = useState<string>('all');
  const [selectedSentiment, setSelectedSentiment] = useState<string>('all');
  const [selectedImpact, setSelectedImpact] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadData = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [feedData, statData] = await Promise.all([
        fetchNewsFeed({ limit: 100 }),
        fetchNewsStatus().catch(() => null),
      ]);
      setArticles(feedData.articles || []);
      if (statData) setStatusInfo(statData);
    } catch (err: any) {
      setError(err.message || 'Failed to load news intelligence feed.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 60000); // 1 minute background poll
    return () => clearInterval(interval);
  }, []);

  // Filtered articles
  const filteredArticles = useMemo(() => {
    return articles.filter((art) => {
      // Tab filter
      if (selectedTab === 'portfolio' && !art.is_portfolio_relevant) return false;
      if (selectedTab === 'crypto' && art.category !== 'crypto') return false;
      if (selectedTab === 'company' && art.category !== 'company' && art.category !== 'earnings') return false;
      if (selectedTab === 'macro' && art.category !== 'macro' && art.category !== 'monetary_policy') return false;
      if (selectedTab === 'regulation' && art.category !== 'regulation') return false;
      if (selectedTab === 'earnings' && art.category !== 'earnings') return false;

      // Sentiment filter
      if (selectedSentiment !== 'all' && art.sentiment_label !== selectedSentiment) return false;

      // Impact filter
      if (selectedImpact !== 'all' && art.impact_level !== selectedImpact) return false;

      // Text search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inHeadline = art.headline.toLowerCase().includes(q);
        const inSummary = art.summary ? art.summary.toLowerCase().includes(q) : false;
        const inAssets = art.related_assets.some((ra) => ra.symbol.toLowerCase().includes(q) || (ra.name && ra.name.toLowerCase().includes(q)));
        const inPublisher = art.publisher ? art.publisher.toLowerCase().includes(q) : false;
        if (!inHeadline && !inSummary && !inAssets && !inPublisher) return false;
      }

      return true;
    });
  }, [articles, selectedTab, selectedSentiment, selectedImpact, searchQuery]);

  const portfolioCount = useMemo(() => articles.filter((a) => a.is_portfolio_relevant).length, [articles]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-100">Financial News Intelligence</h2>
            <Badge variant="blue" size="sm">Phase 2B Live</Badge>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Deduplicated financial news, entity mapping, and market impact classification.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData(true)}
            disabled={refreshing || loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 border border-gray-800 text-xs text-gray-300 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin text-blue-400' : ''}`} />
            <span>{refreshing ? 'Syncing...' : 'Refresh Feed'}</span>
          </button>
        </div>
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
          <div className="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Total Cached Stories</div>
          <div className="text-2xl font-bold text-gray-100 mt-1">{articles.length}</div>
          <div className="text-[10px] text-gray-500 mt-0.5">Deduplicated from active feeds</div>
        </div>

        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
          <div className="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Portfolio Relevant</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{portfolioCount}</div>
          <div className="text-[10px] text-gray-500 mt-0.5">Matches held OKX assets</div>
        </div>

        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
          <div className="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Active Providers</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">
            {statusInfo?.active_sources?.length ?? 2}
          </div>
          <div className="text-[10px] text-gray-500 mt-0.5">Finnhub + Public RSS</div>
        </div>

        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
          <div className="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Provenance Policy</div>
          <div className="flex items-center gap-1.5 text-xs text-gray-200 mt-2 font-medium">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Zero Fabrication</span>
          </div>
          <div className="text-[10px] text-gray-500 mt-0.5">Real verified sources only</div>
        </div>
      </div>

      {/* Filter Tabs & Controls */}
      <div className="space-y-3">
        {/* Category Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-gray-800/80">
          {[
            { id: 'all', label: 'All Stories' },
            { id: 'portfolio', label: `Portfolio Relevant (${portfolioCount})` },
            { id: 'crypto', label: 'Crypto' },
            { id: 'company', label: 'US Equities' },
            { id: 'earnings', label: 'Earnings' },
            { id: 'macro', label: 'Macro & Rates' },
            { id: 'regulation', label: 'Regulation' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                selectedTab === tab.id
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search & Dropdown Filters */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search news by keyword, symbol (e.g. BTC, NVDA, AAPL), or publisher..."
              className="w-full bg-gray-900/90 border border-gray-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500/50"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select
              value={selectedSentiment}
              onChange={(e) => setSelectedSentiment(e.target.value)}
              className="bg-gray-900/90 border border-gray-800 rounded-lg px-2.5 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-blue-500/50"
            >
              <option value="all">Sentiment: All</option>
              <option value="positive">Positive</option>
              <option value="neutral">Neutral</option>
              <option value="negative">Negative</option>
              <option value="mixed">Mixed</option>
            </select>

            <select
              value={selectedImpact}
              onChange={(e) => setSelectedImpact(e.target.value)}
              className="bg-gray-900/90 border border-gray-800 rounded-lg px-2.5 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-blue-500/50"
            >
              <option value="all">Impact: All</option>
              <option value="high">High Impact</option>
              <option value="medium">Medium Impact</option>
              <option value="low">Low Impact</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main News List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="p-5 rounded-xl bg-gray-900/40 border border-gray-800 animate-pulse space-y-3">
              <div className="h-4 bg-gray-800 rounded w-3/4"></div>
              <div className="h-3 bg-gray-800/60 rounded w-1/2"></div>
              <div className="h-3 bg-gray-800/40 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="p-8 text-center rounded-xl bg-red-950/20 border border-red-900/40 text-red-400 text-xs">
          <AlertTriangle className="h-6 w-6 mx-auto mb-2 opacity-80" />
          <p className="font-semibold">{error}</p>
          <p className="mt-1 text-gray-500">Please check provider configuration or retry.</p>
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-gray-900/30 border border-gray-800/60 space-y-2">
          <Newspaper className="h-8 w-8 text-gray-600 mx-auto mb-1" />
          <div className="text-sm font-semibold text-gray-300">No Current News Available</div>
          <p className="text-xs text-gray-500 max-w-md mx-auto">
            No articles match the selected filters from active providers. Zero synthetic or placeholder news articles are generated.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredArticles.map((article) => (
            <div
              key={article.id}
              className={`p-4 rounded-xl border transition-all duration-150 ${
                article.is_portfolio_relevant
                  ? 'bg-gray-900/80 border-emerald-500/30 hover:border-emerald-500/50'
                  : 'bg-gray-900/50 border-gray-800 hover:border-gray-700'
              }`}
            >
              {/* Header Badges Row */}
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs mb-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-gray-300">{article.publisher || article.source}</span>
                  <span className="text-gray-600">•</span>
                  <span className="text-gray-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {timeAgo(article.published_at)}
                  </span>

                  {article.is_portfolio_relevant && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 text-[10px] font-semibold">
                      <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                      Held Portfolio: {article.portfolio_asset_match}
                    </span>
                  )}

                  <span className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-300 text-[10px] uppercase font-mono">
                    {article.category.replace('_', ' ')}
                  </span>
                </div>

                {/* Sentiment & Impact badges */}
                <div className="flex items-center gap-1.5">
                  {/* Sentiment Badge */}
                  {article.sentiment_label === 'positive' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-900/40 text-[10px] font-medium">
                      <TrendingUp className="h-3 w-3" /> Positive
                    </span>
                  )}
                  {article.sentiment_label === 'negative' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-rose-950/60 text-rose-400 border border-rose-900/40 text-[10px] font-medium">
                      <TrendingDown className="h-3 w-3" /> Negative
                    </span>
                  )}
                  {article.sentiment_label === 'neutral' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-gray-800/80 text-gray-400 text-[10px] font-medium">
                      <Minus className="h-3 w-3" /> Neutral
                    </span>
                  )}
                  {article.sentiment_label === 'mixed' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-900/40 text-[10px] font-medium">
                      Mixed
                    </span>
                  )}

                  {/* Impact Badge */}
                  {article.impact_level === 'high' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-semibold">
                      <Flame className="h-3 w-3" /> High Impact
                    </span>
                  )}
                </div>
              </div>

              {/* Headline */}
              <h3 className="text-sm font-semibold text-gray-100 hover:text-blue-400 transition-colors leading-snug">
                <a href={article.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-baseline gap-1.5">
                  <span>{article.headline}</span>
                  <ExternalLink className="h-3 w-3 text-gray-500 inline-block flex-shrink-0" />
                </a>
              </h3>

              {/* Summary Excerpt */}
              {article.summary && (
                <p className="text-xs text-gray-400 mt-1.5 line-clamp-2 leading-relaxed">
                  {article.summary}
                </p>
              )}

              {/* Footer: Related Assets & Action */}
              <div className="flex flex-wrap items-center justify-between gap-3 mt-3 pt-2.5 border-t border-gray-800/60 text-[11px]">
                {/* Related Assets Pills */}
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-gray-500 text-[10px]">Entities:</span>
                  {article.related_assets.length > 0 ? (
                    article.related_assets.map((asset) => (
                      <div key={asset.symbol} className="inline-flex items-center gap-1">
                        <span className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-200 font-mono font-medium text-[10px]">
                          {asset.symbol}
                        </span>
                        {asset.tokenized_symbol && (
                          <span className="px-1 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-900/40 text-[9px] font-mono">
                            {asset.tokenized_symbol} Tokenized
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <span className="text-gray-500 text-[10px]">General Market</span>
                  )}

                  {article.duplicate_count > 1 && (
                    <span className="px-1.5 py-0.5 rounded bg-blue-950/60 text-blue-300 border border-blue-900/40 text-[10px]">
                      {article.duplicate_count} sources syndicated
                    </span>
                  )}
                </div>

                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors font-medium text-[11px]"
                >
                  <span>Read full source on {article.publisher || article.source}</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Compliance Disclaimer Footer */}
      <div className="p-3 rounded-lg bg-gray-950/70 border border-gray-800/80 text-[11px] text-gray-500 space-y-1">
        <div className="font-semibold text-gray-400">Content Integrity & Non-Advisory Notice:</div>
        <p>
          News headlines and summaries are ingested directly from configured provider feeds (Finnhub and curated public publisher RSS). Sentiment scores and impact classifications represent deterministic informational metadata, not price predictions, trade signals, or investment recommendations.
        </p>
      </div>
    </div>
  );
}
