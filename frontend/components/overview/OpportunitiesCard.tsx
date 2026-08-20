import React from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { ShieldAlert, Info } from 'lucide-react';

export const OpportunitiesCard: React.FC = () => {
  return (
    <Card
      title="Opportunity & Risk Detection"
      subtitle="Evidence-backed AI recommendations with invalidation criteria"
      badge={<Badge variant="gray" size="sm">INACTIVE</Badge>}
    >
      <div className="p-5 rounded-lg bg-gray-900/60 border border-gray-800 space-y-3">
        <div className="flex items-center gap-2 text-gray-200 font-semibold text-sm">
          <ShieldAlert className="h-4 w-4 text-amber-400" />
          <span>AI Advisor Not Activated Yet</span>
        </div>

        <p className="text-xs text-gray-400 leading-relaxed">
          Opportunity and risk detection algorithms are currently disabled. No active investment recommendations, BUY/SELL signals, or confidence scores are being generated for this phase.
        </p>

        <div className="p-3 rounded bg-gray-950/60 border border-gray-800 text-[11px] text-gray-400 font-mono space-y-1">
          <div className="flex items-center gap-2 text-gray-300">
            <Info className="h-3.5 w-3.5 text-blue-400" />
            <span>Operating Principle: Data → Analysis → Evidence → Human Decision</span>
          </div>
          <p className="text-[10px] text-gray-500 pt-1">
            Future recommendations will require multi-factor evidence, risk limits, and thesis invalidation criteria before display.
          </p>
        </div>
      </div>
    </Card>
  );
};
