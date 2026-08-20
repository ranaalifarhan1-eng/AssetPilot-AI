import React from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';

export default function NewsPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-gray-100">News Intelligence</h2>
        <p className="text-xs text-gray-400 mt-1">Deduplicated financial news, sentiment analysis, and regulatory feeds.</p>
      </div>

      <Card title="News Processing Pipeline" badge={<Badge variant="amber">PHASE 2 MODULE</Badge>}>
        <div className="p-8 text-center text-xs text-gray-400 space-y-2">
          <p className="font-semibold text-gray-200">News ingestion & relevance filtering scheduled for Phase 2.</p>
        </div>
      </Card>
    </div>
  );
}
