import React from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { TrendingUp, PieChart, ArrowUpRight } from 'lucide-react';

export const PortfolioOverviewCard: React.FC = () => {
  return (
    <Card
      title="Portfolio Overview"
      subtitle="Aggregated holdings across crypto, stocks & cash reserves"
      badge={<Badge variant="amber" size="sm">DEMO DATA</Badge>}
      action={
        <button className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
          Manage <ArrowUpRight className="h-3 w-3" />
        </button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Value Metric */}
        <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800/80">
          <p className="text-xs text-gray-400 font-medium">Total Estimated Value</p>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-gray-100">$24,850.40</span>
            <span className="text-xs font-semibold text-emerald-400 flex items-center">
              <TrendingUp className="h-3 w-3 mr-0.5" /> +4.2%
            </span>
          </div>
          <p className="text-[11px] text-gray-400 mt-1">24h Gain: +$1,002.15</p>
        </div>

        {/* Allocation Breakdown */}
        <div className="p-4 rounded-lg bg-gray-900/60 border border-gray-800/80 md:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-gray-400 font-medium flex items-center gap-1.5">
              <PieChart className="h-3.5 w-3.5 text-blue-400" /> Asset Allocation
            </p>
            <span className="text-[11px] text-gray-400 font-mono">3 Asset Classes</span>
          </div>

          {/* Allocation Progress Bar */}
          <div className="h-2.5 w-full bg-gray-800 rounded-full overflow-hidden flex gap-0.5 my-2">
            <div className="h-full bg-blue-500 rounded-l" style={{ width: '58%' }} title="Crypto (58%)"></div>
            <div className="h-full bg-emerald-500" style={{ width: '27%' }} title="Stocks & ETFs (27%)"></div>
            <div className="h-full bg-amber-500 rounded-r" style={{ width: '15%' }} title="USDT Reserve (15%)"></div>
          </div>

          {/* Asset Allocation Legend */}
          <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-blue-500"></span>
              <span className="text-gray-300 font-medium">Crypto</span>
              <span className="text-gray-400 font-mono ml-auto">58%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              <span className="text-gray-300 font-medium">Stocks</span>
              <span className="text-gray-400 font-mono ml-auto">27%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-amber-500"></span>
              <span className="text-gray-300 font-medium">USDT Reserve</span>
              <span className="text-gray-400 font-mono ml-auto">15%</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
