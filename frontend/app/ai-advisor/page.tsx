import React from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';

export default function AIAdvisorPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-gray-100">AI Market Advisor & Weekly Allocation Assistant</h2>
        <p className="text-xs text-gray-400 mt-1">Evidence-backed investment recommendations, risk scoring, and weekly DCA allocation assistant.</p>
      </div>

      <Card title="AI Recommendation Engine" badge={<Badge variant="purple">PHASE 3 & 4 MODULE</Badge>}>
        <div className="p-8 text-center text-xs text-gray-400 space-y-2">
          <p className="font-semibold text-gray-200">AI Advisor & Weekly Assistant scheduled for Phase 3 & 4.</p>
          <p>Combines quantitative indicators with LLM reasoning to output transparent recommendation theses.</p>
        </div>
      </Card>
    </div>
  );
}
