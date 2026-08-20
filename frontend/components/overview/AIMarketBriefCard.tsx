import React from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { BrainCircuit, Info } from 'lucide-react';

export const AIMarketBriefCard: React.FC = () => {
  return (
    <Card
      title="AI Market Brief"
      subtitle="Synthesized intelligence from news, macro events & technical indicators"
      badge={<Badge variant="purple" size="sm">INACTIVE</Badge>}
    >
      <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800 text-xs text-gray-400 leading-relaxed space-y-3">
        <div className="flex items-center gap-2 text-gray-300 font-semibold">
          <BrainCircuit className="h-4 w-4 text-purple-400" />
          <span>AI Intelligence Engine Not Activated</span>
        </div>
        <p>
          The AI Market Brief pipeline will be enabled in a future phase once quantitative indicator models and financial news deduplication engines are activated.
        </p>
        <div className="p-2.5 rounded bg-gray-950/60 border border-gray-800 text-[11px] text-gray-400 flex items-center gap-2 font-mono">
          <Info className="h-3.5 w-3.5 text-blue-400 flex-shrink-0" />
          <span>Current Status: Standby • Zero automated market analysis generated</span>
        </div>
      </div>
    </Card>
  );
};
