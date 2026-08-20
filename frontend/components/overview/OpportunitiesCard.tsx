import React from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { ShieldAlert, CheckCircle2, ChevronRight, AlertTriangle } from 'lucide-react';

const opportunityItems = [
  {
    asset: 'BTC (Bitcoin)',
    action: 'ACCUMULATE',
    actionVariant: 'green' as const,
    aiScore: 78,
    confidence: 'Medium-High',
    riskLevel: 'Medium',
    riskVariant: 'amber' as const,
    thesis: 'Technical trend holding key support with positive regulatory and macro news alignment.',
    supportingFactors: [
      'Positive news sentiment surrounding spot institutional ETF inflows.',
      'Holding 200-day moving average support at $62,400.',
      'Stablecoin reserves on exchanges reaching 6-month highs.'
    ],
    invalidationCriteria: 'Daily close below $61,500 breaks technical market structure.',
    sources: ['OKX Market Data', 'FRED Macro API', 'CryptoPanic Feed'],
  },
  {
    asset: 'S&P 500 ETF (VOO / Tokenized)',
    action: 'ACCUMULATE',
    actionVariant: 'blue' as const,
    aiScore: 72,
    confidence: 'High',
    riskLevel: 'Low-Medium',
    riskVariant: 'green' as const,
    thesis: 'Broad market earnings momentum remains solid despite interest rate volatility.',
    supportingFactors: [
      '78% of Q2 earnings reports exceeded consensus expectations.',
      'Federal Reserve rate hike cycle at terminal peak.',
    ],
    invalidationCriteria: 'Core inflation prints above 3.5% YoY.',
    sources: ['SEC Filings', 'Yahoo Finance API'],
  },
];

export const OpportunitiesCard: React.FC = () => {
  return (
    <Card
      title="Opportunity & Risk Detection"
      subtitle="Evidence-backed AI recommendations with invalidation criteria"
      badge={<Badge variant="amber" size="sm">DEMO STRUCTURE</Badge>}
    >
      <div className="space-y-4">
        {opportunityItems.map((opp) => (
          <div
            key={opp.asset}
            className="p-4 rounded-lg bg-gray-900/60 border border-gray-800/80 hover:border-gray-700 transition-colors space-y-3"
          >
            {/* Header Info */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-800/60 pb-2.5">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-gray-100">{opp.asset}</span>
                <Badge variant={opp.actionVariant}>{opp.action}</Badge>
              </div>

              {/* Metrics */}
              <div className="flex items-center gap-3 text-xs">
                <div className="flex items-center gap-1">
                  <span className="text-gray-400">AI Score:</span>
                  <span className="font-bold text-blue-400 font-mono">{opp.aiScore}/100</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-gray-400">Confidence:</span>
                  <span className="text-gray-200 font-medium">{opp.confidence}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-gray-400">Risk:</span>
                  <Badge variant={opp.riskVariant} size="sm">{opp.riskLevel}</Badge>
                </div>
              </div>
            </div>

            {/* Rationale & Thesis */}
            <p className="text-xs text-gray-300 leading-relaxed font-medium">{opp.thesis}</p>

            {/* Supporting Factors */}
            <div className="space-y-1">
              <span className="text-[11px] text-gray-400 font-semibold uppercase tracking-wider">Supporting Factors:</span>
              <ul className="space-y-1 text-xs text-gray-300">
                {opp.supportingFactors.map((factor, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Invalidation Trigger */}
            <div className="p-2.5 rounded bg-red-950/20 border border-red-800/30 text-xs text-red-300 flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-semibold text-red-400">Thesis Invalidation Criteria: </span>
                <span>{opp.invalidationCriteria}</span>
              </div>
            </div>

            {/* Sources */}
            <div className="flex items-center justify-between text-[11px] text-gray-400 pt-1">
              <div className="flex items-center gap-2">
                <span>Sources:</span>
                {opp.sources.map((src, i) => (
                  <span key={i} className="bg-gray-800/80 px-2 py-0.5 rounded text-gray-300 font-mono text-[10px]">
                    {src}
                  </span>
                ))}
              </div>
              <button className="text-blue-400 hover:text-blue-300 flex items-center gap-0.5 text-xs font-medium">
                Full Evidence <ChevronRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
