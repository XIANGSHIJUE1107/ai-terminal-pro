'use client';

import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { getFundFlowOverview, getFundFlowTrend } from '@/lib/api';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell,
} from 'recharts';

export default function FundFlowPage() {
  const [overview, setOverview] = useState<any>(null);
  const [trend, setTrend] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [trendDays, setTrendDays] = useState(20);

  useEffect(() => {
    async function load() {
      try {
        const [ov, tr] = await Promise.all([
          getFundFlowOverview(),
          getFundFlowTrend(trendDays),
        ]);
        setOverview(ov);
        setTrend(tr.trend || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [trendDays]);

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="animate-pulse text-terminal-muted">加载中...</div></div>;
  }

  const formatMoney = (val: number) => {
    if (Math.abs(val) >= 1e8) return `${(val / 1e8).toFixed(2)}亿`;
    if (Math.abs(val) >= 1e4) return `${(val / 1e4).toFixed(0)}万`;
    return val?.toFixed(0) || '0';
  };

  const summary = overview?.summary || {};

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold flex items-center gap-2">
        <DollarSign size={20} className="text-terminal-accent" />
        资金流向中心
      </h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="card-terminal p-4">
          <div className="text-xs text-terminal-muted mb-1">主力净流入</div>
          <div className={`text-2xl font-bold font-mono-data ${(summary.total_main_net_inflow || 0) > 0 ? 'price-up' : 'price-down'}`}>
            {formatMoney(summary.total_main_net_inflow || 0)}
          </div>
        </div>
        <div className="card-terminal p-4">
          <div className="text-xs text-terminal-muted mb-1">超大单净流入</div>
          <div className={`text-2xl font-bold font-mono-data ${(summary.total_super_large || 0) > 0 ? 'price-up' : 'price-down'}`}>
            {formatMoney(summary.total_super_large || 0)}
          </div>
        </div>
        <div className="card-terminal p-4">
          <div className="text-xs text-terminal-muted mb-1">大单净流入</div>
          <div className={`text-2xl font-bold font-mono-data ${(summary.total_large || 0) > 0 ? 'price-up' : 'price-down'}`}>
            {formatMoney(summary.total_large || 0)}
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="card-terminal p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <BarChart3 size={16} className="text-terminal-accent-blue" />
            资金趋势曲线
          </h3>
          <div className="flex gap-1">
            {[5, 20, 60, 120].map(d => (
              <button
                key={d}
                onClick={() => setTrendDays(d)}
                className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                  trendDays === d
                    ? 'border-terminal-accent text-terminal-accent bg-terminal-accent/10'
                    : 'border-terminal-border text-terminal-muted'
                }`}
              >
                近{d}日
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#111827', border: '1px solid #1e293b', borderRadius: '8px' }}
            />
            <Area type="monotone" dataKey="main_net_inflow" stroke="#00c853" fill="#00c853" fillOpacity={0.1} name="主力净流入" />
            <Area type="monotone" dataKey="super_large_net" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.1} name="超大单" />
            <Area type="monotone" dataKey="large_net" stroke="#f0b90b" fill="#f0b90b" fillOpacity={0.1} name="大单" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Top Inflows / Outflows */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card-terminal p-4">
          <h3 className="text-sm font-medium mb-2 price-up flex items-center gap-1">
            <TrendingUp size={14} /> 资金流入TOP10
          </h3>
          <div className="space-y-1">
            {(overview?.top_inflows || []).slice(0, 10).map((item: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-1 text-xs">
                <span className="text-terminal-text">{item.sector_name}</span>
                <span className="price-up font-mono-data">{formatMoney(item.main_net_inflow || 0)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card-terminal p-4">
          <h3 className="text-sm font-medium mb-2 price-down flex items-center gap-1">
            <TrendingDown size={14} /> 资金流出TOP10
          </h3>
          <div className="space-y-1">
            {(overview?.top_outflows || []).slice(0, 10).map((item: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-1 text-xs">
                <span className="text-terminal-text">{item.sector_name}</span>
                <span className="price-down font-mono-data">{formatMoney(item.main_net_inflow || 0)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}