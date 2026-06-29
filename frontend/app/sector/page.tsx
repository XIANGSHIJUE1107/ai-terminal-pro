'use client';

import { useEffect, useState } from 'react';
import { PieChart, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import { getSectorRankings, getHotSectors } from '@/lib/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell,
} from 'recharts';

export default function SectorPage() {
  const [rankings, setRankings] = useState<any[]>([]);
  const [hotSectors, setHotSectors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('main_net_inflow');

  useEffect(() => {
    async function load() {
      try {
        const [rk, hs] = await Promise.all([
          getSectorRankings(sortBy, 30),
          getHotSectors(),
        ]);
        setRankings(rk.rankings || []);
        setHotSectors(hs.hot_sectors || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [sortBy]);

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="animate-pulse text-terminal-muted">加载中...</div></div>;
  }

  const formatMoney = (val: number) => {
    if (Math.abs(val) >= 1e8) return `${(val / 1e8).toFixed(2)}亿`;
    if (Math.abs(val) >= 1e4) return `${(val / 1e4).toFixed(0)}万`;
    return val?.toFixed(0) || '0';
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold flex items-center gap-2">
        <PieChart size={20} className="text-terminal-accent" />
        行业板块分析中心
      </h1>

      {/* Hot Sectors */}
      <div className="card-terminal p-4">
        <h3 className="text-sm font-medium mb-3">热门题材</h3>
        <div className="flex flex-wrap gap-2">
          {['机器人', 'AI', '算力', '半导体', '军工', '商业航天', '消费电子', '光模块', '新能源', '创新药'].map(tag => (
            <span key={tag} className="px-3 py-1 text-xs rounded-full bg-terminal-accent/10 text-terminal-accent border border-terminal-accent/20">
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Rankings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card-terminal p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <BarChart3 size={16} className="text-terminal-accent-blue" />
              资金流向排行
            </h3>
            <div className="flex gap-1">
              {[
                { key: 'main_net_inflow', label: '主力净流入' },
                { key: 'change_pct', label: '涨跌幅' },
              ].map(opt => (
                <button
                  key={opt.key}
                  onClick={() => setSortBy(opt.key)}
                  className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                    sortBy === opt.key
                      ? 'border-terminal-accent text-terminal-accent bg-terminal-accent/10'
                      : 'border-terminal-border text-terminal-muted'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={rankings.slice(0, 20)} layout="vertical" margin={{ left: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis type="category" dataKey="sector_name" tick={{ fontSize: 10, fill: '#64748b' }} width={60} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', border: '1px solid #1e293b', borderRadius: '8px' }}
              />
              <Bar dataKey={sortBy} radius={[0, 4, 4, 0]}>
                {rankings.slice(0, 20).map((entry, i) => (
                  <Cell
                    key={i}
                    fill={(entry[sortBy] || 0) > 0 ? '#00c853' : '#ff1744'}
                    fillOpacity={0.6}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card-terminal p-4">
          <h3 className="text-sm font-medium mb-3">全部板块</h3>
          <div className="space-y-1 max-h-[450px] overflow-y-auto">
            {rankings.map((item, i) => {
              const isPos = (item.main_net_inflow || 0) > 0;
              return (
                <div key={i} className="flex items-center justify-between py-1.5 border-b border-terminal-border/30 last:border-0 hover:bg-terminal-hover/20 px-1 rounded">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-terminal-muted w-4">{i + 1}</span>
                    <span className="text-xs text-terminal-text">{item.sector_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-mono-data ${isPos ? 'price-up' : 'price-down'}`}>
                      {formatMoney(item.main_net_inflow || 0)}
                    </span>
                    <span className={`text-xs font-mono-data ${(item.change_pct || 0) > 0 ? 'price-up' : 'price-down'}`}>
                      {(item.change_pct || 0).toFixed(2)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}