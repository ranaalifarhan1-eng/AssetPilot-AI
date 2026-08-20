'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, Activity, RefreshCw, X, Coins, Building2, Layers } from 'lucide-react';
import { Badge } from './Badge';
import { fetchSupportedAssets, AssetInfo } from '@/lib/api';
import Link from 'next/link';

export const Header: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<AssetInfo[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsSearching(true);
        const results = await fetchSupportedAssets(undefined, searchQuery.trim());
        setSearchResults(results);
        setShowDropdown(true);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsSearching(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-16 border-b border-gray-800 bg-[#0d121f]/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Search Input with Multi-Asset Autocomplete Dropdown */}
      <div className="relative w-80" ref={dropdownRef}>
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => {
            if (searchResults.length > 0) setShowDropdown(true);
          }}
          placeholder="Search crypto, stocks, tokenized assets..."
          className="w-full bg-gray-900/80 border border-gray-800 rounded-lg pl-9 pr-8 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500/50 transition-colors font-sans"
        />
        {searchQuery && (
          <button
            onClick={() => {
              setSearchQuery('');
              setShowDropdown(false);
            }}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}

        {/* Autocomplete Results Dropdown */}
        {showDropdown && (
          <div className="absolute top-full left-0 right-0 mt-1.5 bg-gray-900 border border-gray-800 rounded-xl shadow-2xl overflow-hidden max-h-80 overflow-y-auto z-50 divide-y divide-gray-800/60">
            {isSearching ? (
              <div className="p-3 text-center text-xs text-gray-400 font-mono">Searching assets catalog...</div>
            ) : searchResults.length > 0 ? (
              searchResults.map((asset) => {
                let badgeVariant: 'blue' | 'green' | 'purple' = 'blue';
                let Icon = Coins;
                let targetUrl = '/markets';

                if (asset.category === 'equity') {
                  badgeVariant = 'green';
                  Icon = Building2;
                  targetUrl = '/markets';
                } else if (asset.category === 'tokenized_equity') {
                  badgeVariant = 'purple';
                  Icon = Layers;
                  targetUrl = '/markets';
                }

                return (
                  <Link
                    key={asset.internal_id}
                    href={targetUrl}
                    onClick={() => setShowDropdown(false)}
                    className="p-2.5 flex items-center justify-between hover:bg-gray-800/60 transition-colors text-xs block group"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="p-1.5 rounded-lg bg-gray-800 border border-gray-700/60 text-gray-300">
                        <Icon className="h-3.5 w-3.5" />
                      </div>
                      <div>
                        <div className="font-bold text-gray-100 group-hover:text-blue-400 transition-colors flex items-center gap-1.5">
                          <span>{asset.symbol}</span>
                          <span className="text-[10px] text-gray-400 font-normal">({asset.venue})</span>
                        </div>
                        <div className="text-[10px] text-gray-400 truncate max-w-[170px]">{asset.name}</div>
                      </div>
                    </div>

                    <Badge variant={badgeVariant} size="sm">
                      {asset.category === 'tokenized_equity' ? 'Tokenized' : asset.category.toUpperCase()}
                    </Badge>
                  </Link>
                );
              })
            ) : (
              <div className="p-3 text-center text-xs text-gray-500 font-mono">No matching assets found.</div>
            )}
          </div>
        )}
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
