'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { fetchNewsFeed, NewsArticle } from '@/lib/api';
import {
  Newspaper,
  ExternalLink,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowRight,
  Flame,
  CheckCircle2,
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

export const MarketIntelligenceCard: React.FC = () => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    fetchNewsFeed({ limit: 3 })
      .then((data) => {
        if (isMounted) {
          setArticles(data.articles || []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <Card
      title="Latest Market Intelligence"
      subtitle="Deduplicated news feeds, regulatory updates & market sentiment"
      badge={
        <div className="flex items-center gap-2">
          <Badge variant="green" size="sm">LIVE FEED</Badge>
          <Link
            href="/news"
            className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium transition-colors"
          >
            <span>View All News</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      }
    >
      {loading ? (
        <div className="space-y-3 p-2">
          {[1, 2, 3].map((n) => (
            <div key={n} className="p-3 rounded-lg bg-gray-900/40 border border-gray-800 animate-pulse space-y-2">
              <div className="h-3 bg-gray-800 rounded w-2/3"></div>
              <div className="h-2.5 bg-gray-800/60 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      ) : articles.length === 0 ? (
        <div className="p-6 text-center rounded-lg bg-gray-900/40 border border-gray-800 text-xs text-gray-400 space-y-1">
          <Newspaper className="h-5 w-5 text-gray-500 mx-auto mb-1" />
          <p className="font-semibold text-gray-300">No recent market news collected</p>
          <p className="text-[11px] text-gray-500">
            Awaiting next ingestion cycle from Finnhub and public RSS feeds.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {articles.map((article) => (
            <div
              key={article.id}
              className={`p-3 rounded-lg border transition-all ${
                article.is_portfolio_relevant
                  ? 'bg-gray-900/70 border-emerald-500/30 hover:border-emerald-500/50'
                  : 'bg-gray-900/40 border-gray-800 hover:border-gray-700'
              }`}
            >
              <div className="flex items-center justify-between gap-2 text-[11px] text-gray-400 mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-300">{article.publisher || article.source}</span>
                  <span className="text-gray-600">•</span>
                  <span className="flex items-center gap-1 text-gray-500">
                    <Clock className="h-3 w-3" />
                    {timeAgo(article.published_at)}
                  </span>
                  {article.is_portfolio_relevant && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 text-[9px] font-semibold">
                      <CheckCircle2 className="h-2.5 w-2.5 text-emerald-400" />
                      Held: {article.portfolio_asset_match}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5">
                  {article.sentiment_label === 'positive' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 text-[10px]">
                      <TrendingUp className="h-2.5 w-2.5" /> Positive
                    </span>
                  )}
                  {article.sentiment_label === 'negative' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-rose-950/60 text-rose-400 text-[10px]">
                      <TrendingDown className="h-2.5 w-2.5" /> Negative
                    </span>
                  )}
                  {article.sentiment_label === 'neutral' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-gray-800/80 text-gray-400 text-[10px]">
                      <Minus className="h-2.5 w-2.5" /> Neutral
                    </span>
                  )}
                  {article.impact_level === 'high' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 text-[10px] font-semibold">
                      <Flame className="h-2.5 w-2.5" /> High Impact
                    </span>
                  )}
                </div>
              </div>

              <h4 className="text-xs font-semibold text-gray-100 hover:text-blue-400 transition-colors leading-snug">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-baseline gap-1"
                >
                  <span>{article.headline}</span>
                  <ExternalLink className="h-2.5 w-2.5 text-gray-500 inline-block flex-shrink-0" />
                </a>
              </h4>

              {article.summary && (
                <p className="text-[11px] text-gray-400 mt-1 line-clamp-1">
                  {article.summary}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
