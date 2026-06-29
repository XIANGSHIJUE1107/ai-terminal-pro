'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Star, Plus, Trash2, TrendingUp, TrendingDown, Edit3 } from 'lucide-react';
import { getWatchlist, deleteFromWatchlist, addToWatchlist, getPortfolioSummary } from '@/lib/api';

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [portfolio, setPortfolio] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [showAdd, setShowAdd] = useState(false);
  const [newStock, setNewStock] = useState({ symbol: '', name: '', market: 'A', tags: '[]' });

  useEffect(() => {
    async function load() {
      try {
        const [wl, pf] = await Promise.all([
          getWatchlist(),
          getPortfolioSummary(),
        ]);
        setWatchlist(wl.watchlist || []);
        setPortfolio(pf.stocks || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await deleteFromWatchlist(id);
      setWatchlist(prev => prev.filter(w => w.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleAdd = async () => {
    if (!newStock.symbol || !newStock.name) return;
    try {
      await addToWatchlist(newStock);
      setShowAdd(false);
      setNewStock({ symbol: '', name: '', market: 'A', tags: '[]' });
      const wl = await getWatchlist();
      setWatchlist(wl.watchlist || []);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="animate-pulse text-terminal-muted">加载中...</div></div>;
  }

  const markets = ['all', 'A', 'HK', 'US', 'ETF', 'INDEX'];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-terminal-text flex items-center gap-2">
          <Star size={20} className="text-terminal-accent" />
          自选股管理
        </h1>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-accent flex items-center gap-1">
          <Plus size={14} /> 添加标的
        </button>
      </div>

      {/* Add Form */}
      {showAdd && (
        <div className="card-terminal p-4 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <input
              className="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm text-terminal-text focus:border-terminal-accent outline-none"
              placeholder="代码 (如600487)"
              value={newStock.symbol}
              onChange={e => setNewStock({ ...newStock, symbol: e.target.value })}
            />
            <input
              className="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm text-terminal-text focus:border-terminal-accent outline-none"
              placeholder="名称"
              value={newStock.name}
              onChange={e => setNewStock({ ...newStock, name: e.target.value })}
            />
            <select
              className="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm text-terminal-text outline-none"
              value={newStock.market}
              onChange={e => setNewStock({ ...newStock, market: e.target.value })}
            >
              {['A', 'HK', 'US', 'ETF', 'INDEX', 'SECTOR', 'FUTURE', 'GOLD', 'FX', 'CRYPTO'].map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <button onClick={handleAdd} className="btn-blue">确认添加</button>
          </div>
        </div>
      )}

      {/* Market Tabs */}
      <div className="flex gap-2">
        {markets.map(m => (
          <button
            key={m}
            onClick={() => setActiveTab(m)}
            className={`px-3 py-1 text-xs rounded border transition-colors ${
              activeTab === m
                ? 'border-terminal-accent text-terminal-accent bg-terminal-accent/10'
                : 'border-terminal-border text-terminal-muted hover:text-terminal-text'
            }`}
          >
            {m === 'all' ? '全部' : m}
          </button>
        ))}
      </div>

      {/* Watchlist Table */}
      <div className="card-terminal overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-terminal-border text-xs text-terminal-muted">
              <th className="text-left p-3 w-8">#</th>
              <th className="text-left p-3">名称</th>
              <th className="text-left p-3">代码</th>
              <th className="text-left p-3">市场</th>
              <th className="text-right p-3">最新价</th>
              <th className="text-right p-3">涨跌幅</th>
              <th className="text-right p-3">标签</th>
              <th className="text-center p-3 w-20">操作</th>
            </tr>
          </thead>
          <tbody>
            {watchlist
              .filter(w => activeTab === 'all' || w.market === activeTab)
              .map((item, i) => {
                const priceData = portfolio.find(p => p.symbol === item.symbol);
                const isUp = (priceData?.change_pct || 0) > 0;
                const isDown = (priceData?.change_pct || 0) < 0;
                return (
                  <tr key={item.id} className="border-b border-terminal-border/50 hover:bg-terminal-hover/20 transition-colors">
                    <td className="p-3 text-xs text-terminal-muted">{i + 1}</td>
                    <td className="p-3">
                      <Link href={`/stock/${item.symbol}`} className="text-sm text-terminal-text hover:text-terminal-accent transition-colors">
                        {item.name}
                      </Link>
                    </td>
                    <td className="p-3 text-xs text-terminal-muted font-mono-data">{item.symbol}</td>
                    <td className="p-3">
                      <span className="text-xs px-1.5 py-0.5 rounded bg-terminal-accent/10 text-terminal-accent">{item.market}</span>
                    </td>
                    <td className={`p-3 text-sm text-right font-mono-data ${isUp ? 'price-up' : isDown ? 'price-down' : ''}`}>
                      {priceData?.close?.toFixed(2) || '--'}
                    </td>
                    <td className={`p-3 text-sm text-right font-mono-data flex items-center justify-end gap-1 ${
                      isUp ? 'price-up' : isDown ? 'price-down' : ''
                    }`}>
                      {isUp ? <TrendingUp size={12} /> : isDown ? <TrendingDown size={12} /> : null}
                      {priceData ? `${isUp ? '+' : ''}${priceData.change_pct.toFixed(2)}%` : '--'}
                    </td>
                    <td className="p-3 text-right">
                      <span className="text-xs text-terminal-muted">{item.tags || '-'}</span>
                    </td>
                    <td className="p-3 text-center">
                      <button onClick={() => handleDelete(item.id)} className="text-terminal-muted hover:text-terminal-red transition-colors">
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
        {watchlist.filter(w => activeTab === 'all' || w.market === activeTab).length === 0 && (
          <div className="text-center py-12 text-terminal-muted text-sm">暂无自选股数据</div>
        )}
      </div>
    </div>
  );
}