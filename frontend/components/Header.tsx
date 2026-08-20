'use client';

import React from 'react';
import { Search, Activity, RefreshCw } from 'lucide-react';
import { Badge } from './Badge';

export const Header: React.FC = () => {
  return (
    <header className="h-16 border-b border-gray-800 bg-[#0d121f]/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-10">
      {/* Search Input Placeholder */}
      <div className="relative w-80">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search crypto, stocks, signals..."
          className="w-full bg-gray-900/80 border border-gray-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500/50"
        />
      </div>

      {/* System Status & Controls */}
      <div className="flex items-center gap-4">
        {/* Backend Connectivity Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-800 bg-gray-900/40 text-xs">
          <Activity className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
          <span className="text-gray-300 font-medium">Backend Sync:</span>
          <span className="text-emerald-400 font-mono text-[11px]">Ready</span>
        </div>

        {/* Product Status */}
        <Badge variant="blue" size="sm">
          Read-Only Mode
        </Badge>

        <button
          className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 rounded-lg transition-colors"
          title="Refresh Data"
          onClick={() => window.location.reload()}
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
};
