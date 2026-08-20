import React from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';

export default function MarketsPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-gray-100">Market Explorer</h2>
        <p className="text-xs text-gray-400 mt-1">Crypto tickers, equity benchmarks, technical metrics, and market correlation matrices.</p>
      </div>

      <Card title="Markets Engine" badge={<Badge variant="amber">PHASE 1 MODULE</Badge>}>
        <div className="p-8 text-center text-xs text-gray-400 space-y-2">
          <p className="font-semibold text-gray-200">Market data streaming pipeline scheduled for Phase 1.</p>
          <p>Integrates OKX public ticker data, Yahoo Finance stock feeds, and technical indicators.</p>
        </div>
      </Card>
    </div>
  );
}
