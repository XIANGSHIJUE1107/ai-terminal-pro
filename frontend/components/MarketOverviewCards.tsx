'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface IndexItem {
  code: string;
  name: string;
  close: number;
  change_pct: number;
}

export function MarketOverviewCards({ indices }: { indices: any }) {
  if (!indices) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 xl:grid-cols-8 gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="card-terminal p-3 animate-pulse">
            <div className="h-4 bg-terminal-border rounded w-16 mb-1" />
            <div className="h-5 bg-terminal-border rounded w-20 mb-1" />
            <div className="h-3 bg-terminal-border rounded w-12" />
          </div>
        ))}
      </div>
    );
  }

  const allIndices = [
    ...(indices.a_shares || []),
    ...(indices.hk || []),
    ...(indices.us || []),
    ...(indices.global || []),
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 xl:grid-cols-8 gap-3">
      {allIndices.map((item: IndexItem) => {
        const isUp = item.change_pct > 0;
        const isDown = item.change_pct < 0;
        const Icon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;
        const colorClass = isUp ? 'price-up' : isDown ? 'price-down' : 'price-neutral';

        return (
          <div key={item.code} className="card-terminal p-3 hover:border-terminal-hover transition-all cursor-pointer group">
            <div className="text-xs text-terminal-muted truncate mb-1">{item.name}</div>
            <div className={`text-lg font-bold font-mono-data ${colorClass}`}>
              {item.close.toLocaleString()}
            </div>
            <div className={`flex items-center gap-1 text-xs mt-1 ${colorClass}`}>
              <Icon size={12} />
              <span className="font-mono-data">
                {isUp ? '+' : ''}{item.change_pct.toFixed(2)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}