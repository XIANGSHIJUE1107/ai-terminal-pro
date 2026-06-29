'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';
import { getSectorRankings } from '@/lib/api';

interface SectorItem {
  sector_name: string;
  main_net_inflow: number;
  change_pct: number;
}

export function SectorFlowMini() {
  const [sectors, setSectors] = useState<SectorItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getSectorRankings('main_net_inflow', 10);
        setSectors(data.rankings || []);
      } catch (e) {
        console.error('Sector load error:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="card-terminal p-4 animate-pulse">
        <div className="h-4 bg-terminal-border rounded w-24 mb-3" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-8 bg-terminal-border rounded w-full mb-2" />
        ))}
      </div>
    );
  }

  const formatMoney = (val: number) => {
    if (Math.abs(val) >= 1e8) return `${(val / 1e8).toFixed(2)}亿`;
    if (Math.abs(val) >= 1e4) return `${(val / 1e4).toFixed(0)}万`;
    return val.toFixed(0);
  };

  return (
    <div className="card-terminal p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-terminal-text flex items-center gap-2">
          <BarChart3 size={16} className="text-terminal-accent-blue" />
          行业资金流向 TOP10
        </h3>
        <Link href="/sector" className="text-xs text-terminal-accent-blue hover:underline">
          更多
        </Link>
      </div>
      <div className="space-y-1.5">
        {sectors.map((item, i) => {
          const isPositive = (item.main_net_inflow || 0) > 0;
          return (
            <div key={i} className="flex items-center justify-between py-1.5 border-b border-terminal-border/30 last:border-0 hover:bg-terminal-hover/20 px-1 rounded transition-colors">
              <div className="flex items-center gap-2">
                <span className="text-xs text-terminal-muted w-4">{i + 1}</span>
                <span className="text-xs text-terminal-text">{item.sector_name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs font-mono-data ${isPositive ? 'price-up' : 'price-down'}`}>
                  {isPositive ? '+' : ''}{formatMoney(item.main_net_inflow || 0)}
                </span>
                <span className={`text-xs font-mono-data flex items-center gap-0.5 ${
                  (item.change_pct || 0) > 0 ? 'price-up' : 'price-down'
                }`}>
                  {(item.change_pct || 0) > 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                  {(item.change_pct || 0).toFixed(2)}%
                </span>
              </div>
            </div>
          );
        })}
        {sectors.length === 0 && (
          <div className="text-xs text-terminal-muted text-center py-8">
            暂无板块资金数据
          </div>
        )}
      </div>
    </div>
  );
}