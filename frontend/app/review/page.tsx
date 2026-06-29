'use client';

import { useEffect, useState } from 'react';
import { Activity, Sparkles, Calendar, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getDailyReview } from '@/lib/api';

export default function ReviewPage() {
  const [review, setReview] = useState<any>(null);
  const [aiReview, setAiReview] = useState('');
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getDailyReview();
        setReview(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setAiReview('');
    try {
      const response = await fetch('/api/review/generate/stream');
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          setAiReview(prev => prev + decoder.decode(value));
        }
      }
    } catch (e) {
      setAiReview('AI复盘生成失败，请稍后重试');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="animate-pulse text-terminal-muted">加载中...</div></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Calendar size={20} className="text-terminal-accent" />
          大盘复盘系统
        </h1>
        <button onClick={handleGenerate} disabled={generating} className="btn-accent flex items-center gap-1">
          <Sparkles size={14} />
          {generating ? '生成中...' : 'AI生成复盘'}
        </button>
      </div>

      {/* Market Data */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card-terminal p-4">
          <h3 className="text-sm font-medium mb-2">指数表现</h3>
          <div className="space-y-1">
            {(review?.indices?.a_shares || []).map((idx: any) => (
              <div key={idx.code} className="flex items-center justify-between py-1 text-sm">
                <span className="text-terminal-text">{idx.name}</span>
                <div className="flex items-center gap-3">
                  <span className="font-mono-data">{idx.close}</span>
                  <span className={`font-mono-data ${idx.change_pct > 0 ? 'price-up' : 'price-down'}`}>
                    {idx.change_pct > 0 ? '+' : ''}{idx.change_pct}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card-terminal p-4">
          <h3 className="text-sm font-medium mb-2">板块热力图</h3>
          <div className="space-y-1">
            {(review?.sectors || []).slice(0, 10).map((s: any) => (
              <div key={s.sector_name} className="flex items-center justify-between py-1 text-sm">
                <span className="text-terminal-text">{s.sector_name}</span>
                <div className="flex items-center gap-3">
                  <span className={`font-mono-data ${(s.change_pct || 0) > 0 ? 'price-up' : 'price-down'}`}>
                    {(s.change_pct || 0).toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card-terminal p-4">
        <h3 className="text-sm font-medium mb-2">市场宽度</h3>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-terminal-muted">上涨板块</div>
            <div className="text-xl font-bold price-up">{review?.breadth?.up_sectors || 0}</div>
          </div>
          <div>
            <div className="text-xs text-terminal-muted">下跌板块</div>
            <div className="text-xl font-bold price-down">{review?.breadth?.down_sectors || 0}</div>
          </div>
          <div>
            <div className="text-xs text-terminal-muted">总计板块</div>
            <div className="text-xl font-bold text-terminal-accent">{review?.breadth?.total || 0}</div>
          </div>
        </div>
      </div>

      {/* AI Review */}
      {aiReview && (
        <div className="card-terminal p-4 border-terminal-accent/30">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Sparkles size={16} className="text-terminal-accent" />
            AI复盘报告
          </h3>
          <div className="text-sm text-terminal-text leading-relaxed whitespace-pre-wrap">
            {aiReview}
          </div>
        </div>
      )}
    </div>
  );
}