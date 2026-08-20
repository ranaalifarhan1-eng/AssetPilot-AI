import React from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { Newspaper, ExternalLink, Clock } from 'lucide-react';

const intelligenceItems = [
  {
    id: 1,
    title: 'Federal Reserve Holds Interest Rates Steady, Outlines Balanced Inflation Outlook',
    source: 'Financial News Feed',
    time: '2 hours ago',
    category: 'Macro Economics',
    sentiment: 'Neutral / Positive',
    sentimentVariant: 'green' as const,
    summary: 'The FOMC maintained interest rates within the expected range, noting persistent progress toward employment and inflation targets.',
  },
  {
    id: 2,
    title: 'Spot Bitcoin ETF Net Inflows Exceed $450M in Single Trading Session',
    source: 'Crypto Market Intelligence',
    time: '4 hours ago',
    category: 'Crypto Markets',
    sentiment: 'Positive',
    sentimentVariant: 'green' as const,
    summary: 'Institutional product demand continues steady accumulation, reducing liquid exchange supply.',
  },
  {
    id: 3,
    title: 'Global Semiconductor Index Rebounds 3.1% Following Quarterly Guidance Updates',
    source: 'Equity Market Radar',
    time: '6 hours ago',
    category: 'Tech Equities',
    sentiment: 'Positive',
    sentimentVariant: 'blue' as const,
    summary: 'Stronger-than-expected hardware demand projections triggered broad technology sector buying.',
  },
];

export const MarketIntelligenceCard: React.FC = () => {
  return (
    <Card
      title="Latest Market Intelligence"
      subtitle="Deduplicated news feeds, regulatory updates & market sentiment"
      badge={<Badge variant="amber" size="sm">MOCK NEWS FEED</Badge>}
    >
      <div className="space-y-3">
        {intelligenceItems.map((item) => (
          <div
            key={item.id}
            className="p-3.5 rounded-lg bg-gray-900/60 border border-gray-800/80 hover:border-gray-700 transition-colors space-y-2"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono text-gray-400">{item.category}</span>
                <Badge variant={item.sentimentVariant} size="sm">{item.sentiment}</Badge>
              </div>
              <div className="flex items-center gap-1 text-[11px] text-gray-400">
                <Clock className="h-3 w-3" />
                <span>{item.time}</span>
              </div>
            </div>

            <h4 className="text-xs font-semibold text-gray-100 leading-snug hover:text-blue-400 cursor-pointer transition-colors flex items-start justify-between gap-2">
              <span>{item.title}</span>
              <ExternalLink className="h-3.5 w-3.5 text-gray-400 flex-shrink-0 mt-0.5" />
            </h4>

            <p className="text-xs text-gray-300 line-clamp-2 leading-relaxed">{item.summary}</p>

            <div className="flex items-center justify-between text-[10px] text-gray-400 pt-1 border-t border-gray-800/40">
              <span>Source: <strong className="text-gray-300 font-normal">{item.source}</strong></span>
              <span className="text-gray-400">Relevance Score: 94%</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
