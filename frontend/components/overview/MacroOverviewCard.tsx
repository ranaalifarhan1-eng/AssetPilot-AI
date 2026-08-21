'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../Card';
import { Badge } from '../Badge';
import { fetchUpcomingMacro, EconomicEvent } from '@/lib/api';
import { Globe, Clock, ShieldCheck, ArrowUpRight, Calendar, ExternalLink } from 'lucide-react';
import Link from 'next/link';

export const MacroOverviewCard: React.FC = () => {
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchUpcomingMacro('30d', 3)
      .then((data) => setEvents(data))
      .catch((err) => console.error('Error fetching overview macro events:', err))
      .finally(() => setLoading(false));
  }, []);

  const formatTime = (utcStr: string) => {
    try {
      const d = new Date(utcStr);
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return utcStr;
    }
  };

  const formatRelativeTime = (utcStr: string) => {
    try {
      const d = new Date(utcStr);
      const now = new Date();
      const diffMs = d.getTime() - now.getTime();
      const diffHrs = Math.round(diffMs / (1000 * 60 * 60));
      const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

      if (diffMs > 0) {
        if (diffHrs < 24) return `In ${Math.max(1, diffHrs)}h`;
        return `In ${diffDays}d`;
      }
      return 'Today';
    } catch {
      return '';
    }
  };

  return (
    <Card
      title="Upcoming Macro Events"
      subtitle="Key market-moving economic releases & FOMC calendar"
      badge={<Badge variant="blue" size="sm">ECONOMIC CALENDAR</Badge>}
      action={
        <Link
          href="/macro"
          className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
        >
          View Calendar <ArrowUpRight className="h-3 w-3" />
        </Link>
      }
    >
      {loading ? (
        <div className="p-4 rounded-lg bg-gray-900/40 border border-gray-800/60 animate-pulse h-28"></div>
      ) : events.length === 0 ? (
        <div className="p-6 text-center text-xs text-gray-400 font-mono">
          No scheduled high-impact events in the next 30 days.
        </div>
      ) : (
        <div className="space-y-2.5">
          {events.map((event) => (
            <div
              key={event.id}
              className="p-2.5 rounded-lg bg-gray-900/60 border border-gray-800 flex items-center justify-between gap-3 text-xs hover:bg-gray-900/90 transition-colors"
            >
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[9px] px-1.5 py-0.2 rounded font-bold font-mono uppercase ${
                      event.importance === 'high'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {event.importance}
                  </span>
                  <span className="text-[10px] text-gray-400 font-mono">
                    {event.category}
                  </span>
                  <span className="text-[10px] text-blue-400 font-mono flex items-center gap-0.5">
                    <Clock className="h-3 w-3" /> {formatTime(event.scheduled_at)}
                  </span>
                </div>

                <div className="font-bold text-gray-100 truncate flex items-center gap-1.5">
                  <span className="truncate">{event.indicator_name || event.event_name}</span>
                  {event.period && (
                    <span className="text-[10px] text-gray-400 font-mono font-normal flex-shrink-0">
                      ({event.period})
                    </span>
                  )}
                </div>

                {event.portfolio_exposure.length > 0 && (
                  <div className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3" /> Portfolio Exposure: {event.portfolio_exposure.join(', ')}
                  </div>
                )}
              </div>

              <div className="text-right font-mono flex-shrink-0 space-y-0.5">
                <div className="text-[11px] font-bold text-emerald-400">
                  {formatRelativeTime(event.scheduled_at)}
                </div>
                {event.forecast !== null ? (
                  <div className="text-[10px] text-gray-400">
                    Est: {event.forecast}{event.unit}
                  </div>
                ) : (
                  <div className="text-[10px] text-gray-500">
                    Consensus: —
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
