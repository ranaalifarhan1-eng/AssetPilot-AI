import React from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';

export default function PortfolioPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-gray-100">Portfolio Tracking</h2>
        <p className="text-xs text-gray-400 mt-1">Multi-asset balances, risk concentration, and OKX read-only integration.</p>
      </div>

      <Card title="Portfolio Manager" badge={<Badge variant="amber">PHASE 1 MODULE</Badge>}>
        <div className="p-8 text-center text-xs text-gray-400 space-y-2">
          <p className="font-semibold text-gray-200">Portfolio tracking module scheduled for Phase 1 implementation.</p>
          <p>Will connect read-only OKX API, stock accounts, and tokenized stock holdings.</p>
        </div>
      </Card>
    </div>
  );
}
