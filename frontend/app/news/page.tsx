'use client';

import { useEffect, useState } from 'react';
import { Newspaper, Sparkles, TrendingUp, TrendingDown, Minus, Search, Filter } from 'lucide-react';
import { getNewsList, analyzeNews, getNewsSentimentStats } from '@/lib/api';

export default function NewsPage() {
  const [news, setNews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState<number | null>(null);
  const [stats, setStats] = useState<any[]>([]);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const [nl, st] = await Promise.all([
          getNewsList(100),
          getNewsSentimentStats(),
        ]);
        setNews(nl.news || []);
        setStats(st.stats || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleAnalyze = async (id: number) => {
    setAnalyzing(id);
    try {
      await analyzeNews(id);
      const nl = await getNewsList(100);
      setNews(nl.news || []);
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(null);
    }
  };

  const sentimentIcon = (s: string) => {
    if (s === 'positive') return <TrendingUp size={14} className="price-up" />;
    if (s === 'negative') return <TrendingDown size={14} className="price-down" />;
    return <Minus size={14} className="text-terminal-muted" />;
  };

  const sentimentBadge = (s: string) => {
    const config: Record<string, string> = {
      positive: 'bg-terminal-green/10 text-terminal-green border-terminal-green/20',
      negative: 'bg-terminal-red/10 text-terminal-red border-terminal-red/20',
      neutral: 'bg-terminal-muted/10 text-terminal-muted border-terminal-muted/20',
    };
    return `px-1.5 py-0.5 rounded text-xs border ${config[s] || config.neutral}`;
  };

  const filteredNews = news.filter(n => {
    if (filter === 'positive' && n.sentiment !== 'positive') return false;
    if (filter === 'negative' && n.sentiment !== 'negative') return false;
    if (searchQuery && !n.content.includes(searchQuery)) return false;
    return true;
  });

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="animate-pulse text-terminal-muted">加载中...</div></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Newspaper size={20} className="text-terminal-accent" />
          AI新闻分析中心
        </h1>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card-terminal p-3 text-center">
          <div className="text-xs text-terminal-muted">总新闻数</div>
          <div className="text-lg font-bold font-mono-data text-terminal-accent">{news.length}</div>
        </div>
        {stats.map(s => (
          <div key={s.sentiment} className="card-terminal p-3 text-center">
            <div className="text-xs text-terminal-muted">
              {s.sentiment === 'positive' ? '利好' : s.sentiment === 'negative' ? '利空' : '中性'}
            </div>
            <div className={`text-lg font-bold font-mono-data ${
              s.sentiment === 'positive' ? 'price-up' : s.sentiment === 'negative' ? 'price-down' : 'text-terminal-muted'
            }`}>
              {s.count}
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          {['all', 'positive', 'negative', 'neutral'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded border transition-colors ${
                filter === f
                  ? 'border-terminal-accent text-terminal-accent bg-terminal-accent/10'
                  : 'border-terminal-border text-terminal-muted hover:text-terminal-text'
              }`}
            >
              {f === 'all' ? '全部' : f === 'positive' ? '利好' : f === 'negative' ? '利空' : '中性'}
            </button>
          ))}
        </div>
        <div className="flex-1" />
        <div className="relative">
          <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-terminal-muted" />
          <input
            className="bg-terminal-bg border border-terminal-border rounded pl-7 pr-3 py-1 text-sm text-terminal-text outline-none focus:border-terminal-accent w-48"
            placeholder="搜索新闻..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* News List */}
      <div className="card-terminal overflow-hidden">
        <div className="divide-y divide-terminal-border/50">
          {filteredNews.map(item => (
            <div key={item.id} className="p-3 hover:bg-terminal-hover/20 transition-colors">
              <div className="flex items-start gap-3">
                <div className="mt-1">
                  {sentimentIcon(item.sentiment || 'neutral')}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-terminal-text leading-relaxed">{item.content}</p>
                  {item.ai_summary && (
                    <div className="mt-1.5 p-2 bg-terminal-bg rounded border border-terminal-border/30">
                      <div className="flex items-center gap-1 mb-1">
                        <Sparkles size={12} className="text-terminal-accent" />
                        <span className="text-xs text-terminal-accent font-medium">AI分析</span>
                      </div>
                      <p className="text-xs text-terminal-text">{item.ai_summary}</p>
                      {item.related_stocks && (
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {JSON.parse(item.related_stocks || '[]').map((s: string, i: number) => (
                            <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-terminal-accent-blue/10 text-terminal-accent-blue">
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-xs text-terminal-muted">{item.ctime}</span>
                    <span className="text-xs text-terminal-muted">{item.source}</span>
                    <span className={sentimentBadge(item.sentiment || 'neutral')}>
                      {item.sentiment === 'positive' ? '利好' : item.sentiment === 'negative' ? '利空' : '中性'}
                    </span>
                  </div>
                </div>
                {!item.sentiment && (
                  <button
                    onClick={() => handleAnalyze(item.id)}
                    disabled={analyzing === item.id}
                    className="btn-blue flex items-center gap-1 text-xs py-1 px-2 flex-shrink-0"
                  >
                    <Sparkles size={12} />
                    {analyzing === item.id ? '分析中...' : 'AI分析'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
        {filteredNews.length === 0 && (
          <div className="text-center py-12 text-terminal-muted text-sm">
            暂无新闻数据
          </div>
        )}
      </div>
    </div>
  );
}