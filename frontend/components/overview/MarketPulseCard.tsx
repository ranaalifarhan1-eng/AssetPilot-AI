import React from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { TrendingUp, TrendingDown } from 'lucide-react';

const marketItems = [
  { symbol: 'BTC/USD', name: 'Bitcoin', price: '$64,250.00', change: '+2.85%', isPositive: true, category: 'Crypto' },
  { symbol: 'ETH/USD', name: 'Ethereum', price: '$3,480.50', change: '+1.42%', isPositive: true, category: 'Crypto' },
  { symbol: 'S&P 500', name: 'US Large Cap Index', price: '5,420.10', change: '-0.32%', isPositive: false, category: 'Macro Equity' },
  { symbol: 'NASDAQ', name: 'Tech Benchmark', price: '17,150.80', change: '+0.88%', isPositive: true, category: 'Tech Equity' },
];

export const MarketPulseCard: React.FC = () => {
  return (
    <Card
      title="Market Pulse"
      subtitle="Reference market benchmarks & core crypto assets"
      badge={<Badge variant="amber" size="sm">DEMO DATA</Badge>}
    >
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {marketItems.map((item) => (
          <div
            key={item.symbol}
            className="p-3.5 rounded-lg bg-gray-900/60 border border-gray-800/80 hover:border-gray-700 transition-colors"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-gray-200">{item.symbol}</span>
              <span className="text-[10px] text-gray-400 font-mono">{item.category}</span>
            </div>
            <p className="text-xs text-gray-400 truncate mb-2">{item.name}</p>
            <div className="flex items-baseline justify-between">
              <span className="text-base font-bold text-gray-100 font-mono">{item.price}</span>
              <span
                className={`text-xs font-semibold flex items-center ${
                  item.isPositive ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {item.isPositive ? (
                  <TrendingUp className="h-3 w-3 mr-0.5" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-0.5" />
                )}
                {item.change}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
