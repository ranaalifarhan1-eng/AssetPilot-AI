'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Wallet,
  TrendingUp,
  BrainCircuit,
  Newspaper,
  Globe,
  Bookmark,
  History,
  Settings,
  ShieldCheck,
} from 'lucide-react';

const navigationItems = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Portfolio', href: '/portfolio', icon: Wallet },
  { name: 'Markets', href: '/markets', icon: TrendingUp },
  { name: 'AI Advisor', href: '/ai-advisor', icon: BrainCircuit },
  { name: 'News Intelligence', href: '/news', icon: Newspaper },
  { name: 'Macro Intelligence', href: '/macro', icon: Globe },
  { name: 'Watchlist', href: '/watchlist', icon: Bookmark },
  { name: 'Signal History', href: '/signals', icon: History },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 border-r border-gray-800 bg-[#0d121f] flex flex-col justify-between h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <BrainCircuit className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-gray-100 tracking-tight">AssetPilot AI</h1>
              <p className="text-[10px] text-gray-400 font-mono tracking-wide uppercase">Market Intelligence</p>
            </div>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-3 space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-blue-400' : 'text-gray-400'}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Safety Policy & Status Badge */}
      <div className="p-4 m-3 rounded-lg border border-gray-800 bg-gray-900/60">
        <div className="flex items-center gap-2 text-emerald-400 text-xs font-medium mb-1">
          <ShieldCheck className="h-4 w-4" />
          <span>Read-Only Operations</span>
        </div>
        <p className="text-[11px] text-gray-400 leading-relaxed">
          Non-custodial intelligence shell. Automated trading disabled.
        </p>
      </div>
    </aside>
  );
};
