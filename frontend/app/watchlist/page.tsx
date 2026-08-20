import React from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';

export default function WatchlistPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-gray-100">Asset Watchlists</h2>
        <p className="text-xs text-gray-400 mt-1">Custom target price alerts and asset monitoring.</p>
      </div>

      <Card title="Watchlists" badge={<Badge variant="amber">PHASE 1 MODULE</Badge>}>
        <div className="p-8 text-center text-xs text-gray-400 space-y-2">
          <p className="font-semibold text-gray-200">Watchlist management scheduled for Phase 1.</p>
        </div>
      </Card>
    </div>
  );
}
