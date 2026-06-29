'use client';

import { useEffect, useState } from 'react';
import { Newspaper, ExternalLink } from 'lucide-react';
import { getNewsList } from '@/lib/api';

interface NewsItem {
  id: number;
  content: string;
  ctime: string;
  source: string;
  sentiment: string;
  ai_summary: string;
}

export function NewsFeed() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getNewsList(20);
        setNews(data.news || []);
      } catch (e) {
        console.error('News load error:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="card-terminal p-4 animate-pulse">
        <div className="h-4 bg-terminal-border rounded w-20 mb-3" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-3 bg-terminal-border rounded w-full mb-2" />
        ))}
      </div>
    );
  }

  return (
    <div className="card-terminal p-4">
      <h3 className="text-sm font-medium text-terminal-text mb-3 flex items-center gap-2">
        <Newspaper size={16} className="text-terminal-accent" />
        实时新闻流
      </h3>
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {news.slice(0, 15).map((item) => {
          const sentimentColor =
            item.sentiment === 'positive' ? 'text-terminal-green' :
            item.sentiment === 'negative' ? 'text-terminal-red' : 'text-terminal-muted';

          return (
            <div key={item.id} className="border-b border-terminal-border/50 pb-2 last:border-0">
              <div className="flex items-start gap-2">
                <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                  item.sentiment === 'positive' ? 'bg-terminal-green' :
                  item.sentiment === 'negative' ? 'bg-terminal-red' : 'bg-terminal-muted'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-terminal-text leading-relaxed line-clamp-2">
                    {item.content}
                  </p>
                  {item.ai_summary && (
                    <p className={`text-xs mt-0.5 ${sentimentColor}`}>
                      AI: {item.ai_summary}
                    </p>
                  )}
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] text-terminal-muted">{item.ctime}</span>
                    <span className="text-[10px] text-terminal-muted">{item.source}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        {(!news || news.length === 0) && (
          <div className="text-xs text-terminal-muted text-center py-8">
            暂无新闻数据，请先运行数据抓取
          </div>
        )}
      </div>
    </div>
  );
}