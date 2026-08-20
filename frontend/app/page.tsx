import React from 'react';
import { PortfolioOverviewCard } from '@/components/overview/PortfolioOverviewCard';
import { MarketPulseCard } from '@/components/overview/MarketPulseCard';
import { AIMarketBriefCard } from '@/components/overview/AIMarketBriefCard';
import { OpportunitiesCard } from '@/components/overview/OpportunitiesCard';
import { MarketIntelligenceCard } from '@/components/overview/MarketIntelligenceCard';

export default function OverviewPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-100 tracking-tight">Market Intelligence & Portfolio Overview</h2>
          <p className="text-xs text-gray-400 mt-1">
            Personal AI Copilot • Crypto, Stocks & Tokenized Market Intelligence
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400 bg-gray-900/80 px-3 py-1.5 rounded-lg border border-gray-800">
          <span>Operating Mode:</span>
          <span className="text-emerald-400 font-medium">Data → Analysis → Evidence → Human Decision</span>
        </div>
      </div>

      {/* Grid Row 1: Portfolio Overview & Market Pulse */}
      <div className="space-y-6">
        <PortfolioOverviewCard />
        <MarketPulseCard />
      </div>

      {/* Grid Row 2: AI Market Brief & Opportunities */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <AIMarketBriefCard />
        </div>
        <div className="lg:col-span-2">
          <OpportunitiesCard />
        </div>
      </div>

      {/* Grid Row 3: Latest Market Intelligence */}
      <div>
        <MarketIntelligenceCard />
      </div>
    </div>
  );
}
