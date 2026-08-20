import React from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { BrainCircuit, Sparkles } from 'lucide-react';

export const AIMarketBriefCard: React.FC = () => {
  return (
    <Card
      title="AI Market Brief"
      subtitle="Synthesized intelligence from news, macro events & technical indicators"
      badge={<Badge variant="purple" size="sm">AI INSIGHT PLACEHOLDER</Badge>}
    >
      <div className="p-4 rounded-lg bg-purple-950/20 border border-purple-800/30 text-xs text-gray-300 leading-relaxed space-y-3">
        <div className="flex items-center gap-2 text-purple-400 font-semibold">
          <Sparkles className="h-4 w-4" />
          <span>Market Intelligence Overview (Synthesized Preview)</span>
        </div>
        <p>
          Bitcoin is consolidating above key moving averages following recent interest rate commentary. Macro liquidity indicators suggest moderate risk-on sentiment across equities and major crypto assets, while volatility indices remain suppressed.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-2 border-t border-purple-800/30 text-[11px]">
          <div className="bg-purple-900/20 p-2 rounded border border-purple-800/20">
            <span className="text-gray-400 block font-medium">Macro Catalyst:</span>
            <span className="text-gray-200 font-mono">Fed Rate Pause Expectations</span>
          </div>
          <div className="bg-purple-900/20 p-2 rounded border border-purple-800/20">
            <span className="text-gray-400 block font-medium">Dominant Trend:</span>
            <span className="text-emerald-400 font-mono">Bullish Accumulation</span>
          </div>
          <div className="bg-purple-900/20 p-2 rounded border border-purple-800/20">
            <span className="text-gray-400 block font-medium">Risk Index:</span>
            <span className="text-amber-400 font-mono">42 / 100 (Moderate)</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
