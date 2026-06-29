'use client';

import Link from 'next/link';
import { TrendingUp, TrendingDown, Minus, ArrowRight } from 'lucide-react';

interface Stock {
  symbol: string;
  name: string;
  close: number;
  change_pct: number;
  volume?: number;
  amount?: number;
}

export function PortfolioMini({ stocks }: { stocks?: Stock[] }) {
  const displayStocks = stocks || [
    { symbol: '600487', name: '亨通光电', close: 0, change_pct: 0 },
    { symbol: '002475', name: '立讯精密', close: 0, change_pct: 0 },
    { symbol: '002384', name: '东山精密', close: 0, change_pct: 0 },
    { symbol: '000988', name: '华工科技', close: 0, change_pct: 0 },
    { symbol: '600459', name: '贵研铂业', close: 0, change_pct: 0 },
    { symbol: '603211', name: '晋拓股份', close: 0, change_pct: 0 },
    { symbol: '600206', name: '有研新材', close: 0, change_pct: 0 },
    { symbol: '000636', name: '风华高科', close: 0, change_pct: 0 },
  ];

  return (
    <div className="card-terminal p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-terminal-text">核心持仓</h3>
        <Link href="/watchlist" className="text-xs text-terminal-accent-blue hover:underline flex items-center gap-1">
          全部 <ArrowRight size={12} />
        </Link>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {displayStocks.map((stock) => {
          const isUp = stock.change_pct > 0;
          const isDown = stock.change_pct < 0;
          const colorClass = isUp ? 'price-up' : isDown ? 'price-down' : 'price-neutral';
          const Icon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;

          return (
            <Link
              key={stock.symbol}
              href={`/stock/${stock.symbol}`}
              className="card-terminal p-3 hover:border-terminal-hover transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-terminal-text truncate">{stock.name}</span>
                <span className="text-xs text-terminal-muted font-mono-data">{stock.symbol}</span>
              </div>
              <div className={`text-lg font-bold font-mono-data ${colorClass}`}>
                {stock.close > 0 ? stock.close.toFixed(2) : '--'}
              </div>
              <div className={`flex items-center gap-1 text-xs mt-1 ${colorClass}`}>
                <Icon size={12} />
                <span className="font-mono-data">
                  {stock.change_pct > 0 ? '+' : ''}{stock.change_pct.toFixed(2)}%
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
