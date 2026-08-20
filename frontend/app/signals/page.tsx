import React from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';

export default function SignalHistoryPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-gray-100">Signal History & Backtesting</h2>
        <p className="text-xs text-gray-400 mt-1">Historical recommendation accuracy tracking (1d, 7d, 30d evaluations).</p>
      </div>

      <Card title="Historical Accuracy Tracking" badge={<Badge variant="amber">PHASE 4 MODULE</Badge>}>
        <div className="p-8 text-center text-xs text-gray-400 space-y-2">
          <p className="font-semibold text-gray-200">Signal history & backtesting scheduled for Phase 4.</p>
          <p>Measures historical returns and confidence calibration for all past AI recommendations.</p>
        </div>
      </Card>
    </div>
  );
}
