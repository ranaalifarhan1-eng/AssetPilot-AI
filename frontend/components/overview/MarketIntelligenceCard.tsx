import React from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { Newspaper, Info } from 'lucide-react';

export const MarketIntelligenceCard: React.FC = () => {
  return (
    <Card
      title="Latest Market Intelligence"
      subtitle="Deduplicated news feeds, regulatory updates & market sentiment"
      badge={<Badge variant="gray" size="sm">INACTIVE</Badge>}
    >
      <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800 space-y-2">
        <div className="flex items-center gap-2 text-gray-300 font-semibold text-xs">
          <Newspaper className="h-4 w-4 text-blue-400" />
          <span>News Intelligence Coming in a Later Phase</span>
        </div>

        <p className="text-xs text-gray-400 leading-relaxed">
          Financial news ingestion, RSS deduplication, and regulatory sentiment tracking will be integrated in Phase 2.
        </p>

        <div className="p-2.5 rounded bg-gray-950/60 border border-gray-800 text-[11px] text-gray-400 flex items-center gap-2 font-mono">
          <Info className="h-3.5 w-3.5 text-blue-400 flex-shrink-0" />
          <span>No fabricated news items or mock financial headlines displayed</span>
        </div>
      </div>
    </Card>
  );
};
