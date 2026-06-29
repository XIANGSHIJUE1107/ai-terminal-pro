'use client';

import { useEffect, useState } from 'react';
import { Zap } from 'lucide-react';

export function NewsTicker() {
  const [news, setNews] = useState<string[]>([]);

  useEffect(() => {
    const defaultNews = [
      '新闻源连接中：请以新闻中心实时聚合结果为准',
      '数据源：新浪财经 / 财联社 / 同花顺，接口不可用时显示来源入口',
    ];
    setNews(defaultNews);
  }, []);

  if (!news.length) return null;

  return (
    <div className="h-7 bg-terminal-card border-b border-terminal-border flex items-center flex-shrink-0 overflow-hidden">
      <div className="flex items-center gap-1 px-2 border-r border-terminal-border h-full flex-shrink-0">
        <Zap size={12} className="text-terminal-accent" />
        <span className="text-xs text-terminal-accent font-medium">电报</span>
      </div>
      <div className="news-ticker-container flex-1 h-full flex items-center">
        <div className="news-ticker-track whitespace-nowrap px-2">
          {news.map((item, i) => (
            <span key={i} className="text-xs text-terminal-muted mr-12 hover:text-terminal-text cursor-pointer transition-colors">
              {item}
            </span>
          ))}
          {news.map((item, i) => (
            <span key={`dup-${i}`} className="text-xs text-terminal-muted mr-12">
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
