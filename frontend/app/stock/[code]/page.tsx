'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { TrendingUp, TrendingDown, Minus, Activity, BarChart3, Cpu } from 'lucide-react';
import { getStockKline, getStockAnalysis, getStockSignals } from '@/lib/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, ComposedChart, Area, Legend,
} from 'recharts';

export default function StockDetailPage() {
  const params = useParams();
  const symbol = params.code as string;

  const [klineData, setKlineData] = useState<any>(null);
  const [analysis, setAnalysis] = useState<string>('');
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activePeriod, setActivePeriod] = useState('daily');
  const [showIndicators, setShowIndicators] = useState<string[]>(['ma', 'volume']);

  useEffect(() => {
    async function load() {
      try {
        const [kl, an, sg] = await Promise.all([
          getStockKline(symbol, 120),
          getStockAnalysis(symbol),
          getStockSignals(symbol),
        ]);
        setKlineData(kl);
        setAnalysis(kl?.analysis || '');
        setSignals(an?.signals || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    if (symbol) load();
  }, [symbol]);

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="animate-pulse text-terminal-muted">加载中...</div></div>;
  }

  if (!klineData?.kline?.length) {
    return <div className="flex items-center justify-center h-full text-terminal-muted">未找到股票数据: {symbol}</div>;
  }

  const latest = klineData.kline[klineData.kline.length - 1];
  const prev = klineData.kline.length > 1 ? klineData.kline[klineData.kline.length - 2] : latest;
  const change = latest.close - prev.close;
  const changePct = prev.close ? (change / prev.close * 100) : 0;
  const isUp = change >= 0;

  const chartData = klineData.kline.map((d: any) => ({
    ...d,
    date: d.date?.slice(5) || d.date,
  }));

  // 成交量颜色
  const volumeColors = chartData.map((d: any) => d.close >= d.open ? '#00c85333' : '#ff174433');

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="card-terminal p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold font-mono-data">{symbol}</h1>
              <span className="text-sm text-terminal-muted">{klineData.name || ''}</span>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className={`text-3xl font-bold font-mono-data ${isUp ? 'price-up' : 'price-down'}`}>
                {latest.close.toFixed(2)}
              </span>
              <div className={`flex items-center gap-1 text-lg ${isUp ? 'price-up' : 'price-down'}`}>
                {isUp ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                <span className="font-mono-data">{isUp ? '+' : ''}{change.toFixed(2)} ({isUp ? '+' : ''}{changePct.toFixed(2)}%)</span>
              </div>
            </div>
          </div>
          <div className="text-right space-y-1">
            <div className="text-xs text-terminal-muted">
              O: <span className="font-mono-data">{latest.open.toFixed(2)}</span>
              {' '}H: <span className="font-mono-data">{latest.high.toFixed(2)}</span>
              {' '}L: <span className="font-mono-data">{latest.low.toFixed(2)}</span>
            </div>
            <div className="text-xs text-terminal-muted">
              成交量: <span className="font-mono-data">{(latest.volume / 10000).toFixed(0)}万手</span>
              {' '}成交额: <span className="font-mono-data">{(latest.amount / 1e8).toFixed(2)}亿</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* K线图 */}
        <div className="lg:col-span-2 card-terminal p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Activity size={16} className="text-terminal-accent" />
              K线图
            </h3>
            <div className="flex gap-1">
              {['1m', '5m', '15m', '30m', '60m', 'daily', 'weekly', 'monthly'].map(p => (
                <button
                  key={p}
                  onClick={() => setActivePeriod(p)}
                  className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                    activePeriod === p
                      ? 'border-terminal-accent text-terminal-accent bg-terminal-accent/10'
                      : 'border-terminal-border text-terminal-muted hover:text-terminal-text'
                  }`}
                >
                  {p === 'daily' ? '日线' : p}
                </button>
              ))}
            </div>
          </div>

          {/* Price Chart */}
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111827',
                  border: '1px solid #1e293b',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                labelStyle={{ color: '#64748b' }}
              />
              <Bar dataKey="volume" fill="#1e293b" opacity={0.3} yAxisId={1} />
              <Line type="monotone" dataKey="close" stroke="#f0b90b" dot={false} strokeWidth={1.5} name="收盘价" />
              {showIndicators.includes('ma') && klineData.ma_data?.length > 0 && (
                <>
                  <Line type="monotone" dataKey="ma5" stroke="#0ea5e9" dot={false} strokeWidth={1} strokeDasharray="3 3" />
                  <Line type="monotone" dataKey="ma10" stroke="#a855f7" dot={false} strokeWidth={1} strokeDasharray="3 3" />
                  <Line type="monotone" dataKey="ma20" stroke="#f97316" dot={false} strokeWidth={1} strokeDasharray="3 3" />
                </>
              )}
            </ComposedChart>
          </ResponsiveContainer>

          {/* Indicator Toggles */}
          <div className="flex gap-1 mt-2">
            {[
              { key: 'ma', label: '均线' },
              { key: 'volume', label: '成交量' },
              { key: 'macd', label: 'MACD' },
              { key: 'kdj', label: 'KDJ' },
              { key: 'rsi', label: 'RSI' },
              { key: 'boll', label: '布林带' },
            ].map(ind => (
              <button
                key={ind.key}
                onClick={() => setShowIndicators(prev =>
                  prev.includes(ind.key) ? prev.filter(i => i !== ind.key) : [...prev, ind.key]
                )}
                className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                  showIndicators.includes(ind.key)
                    ? 'border-terminal-accent-blue text-terminal-accent-blue bg-terminal-accent-blue/10'
                    : 'border-terminal-border text-terminal-muted'
                }`}
              >
                {ind.label}
              </button>
            ))}
          </div>
        </div>

        {/* AI Analysis */}
        <div className="card-terminal p-4">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Cpu size={16} className="text-terminal-accent-blue" />
            AI技术分析
          </h3>
          <div className="text-xs text-terminal-text leading-relaxed whitespace-pre-wrap max-h-[400px] overflow-y-auto">
            {analysis || '正在生成AI分析...'}
          </div>

          {/* 技术指标 */}
          {klineData.indicators && (
            <div className="mt-4 space-y-2 border-t border-terminal-border pt-3">
              <h4 className="text-xs font-medium text-terminal-muted">技术指标摘要</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-terminal-muted">MA5:</span> <span className="font-mono-data">{klineData.indicators.ma5}</span></div>
                <div><span className="text-terminal-muted">MA20:</span> <span className="font-mono-data">{klineData.indicators.ma20}</span></div>
                <div><span className="text-terminal-muted">MACD:</span> <span className="font-mono-data">{klineData.indicators.macd}</span></div>
                <div><span className="text-terminal-muted">RSI(6):</span> <span className="font-mono-data">{klineData.indicators.rsi6}</span></div>
                <div><span className="text-terminal-muted">K:</span> <span className="font-mono-data">{klineData.indicators.k}</span></div>
                <div><span className="text-terminal-muted">D:</span> <span className="font-mono-data">{klineData.indicators.d}</span></div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Signals */}
      <div className="card-terminal p-4">
        <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
          <BarChart3 size={16} className="text-terminal-accent" />
          最近信号
        </h3>
        <div className="flex flex-wrap gap-2">
          {signals.slice(0, 20).map((sig: any, i: number) => (
            <span key={i} className="px-2 py-1 rounded text-xs bg-terminal-accent/10 text-terminal-accent border border-terminal-accent/20">
              {sig.date}: {sig.type} - {sig.detail}
            </span>
          ))}
          {signals.length === 0 && (
            <span className="text-xs text-terminal-muted">暂无信号</span>
          )}
        </div>
      </div>
    </div>
  );
}