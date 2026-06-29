'use client';

import { useEffect, useState } from 'react';
import { Clock, RefreshCw } from 'lucide-react';

export function TopBar() {
  const [time, setTime] = useState('');
  const [marketStatus, setMarketStatus] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleString('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      }));

      const h = now.getHours();
      const m = now.getMinutes();
      const weekday = now.getDay();
      if (weekday === 0 || weekday === 6) {
        setMarketStatus('休市');
      } else if (h < 9 || (h === 9 && m < 30)) {
        setMarketStatus('盘前');
      } else if (h === 9 && m >= 30 || h === 10 || h === 11 && m < 30) {
        setMarketStatus('交易中');
      } else if (h === 11 && m >= 30 && h < 13) {
        setMarketStatus('午休');
      } else if (h >= 13 && h < 15) {
        setMarketStatus('交易中');
      } else {
        setMarketStatus('收盘');
      }
    };
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, []);

  const statusColor = marketStatus === '交易中' ? 'text-terminal-green' :
    marketStatus === '休市' ? 'text-terminal-muted' : 'text-terminal-accent';

  return (
    <header className="h-10 bg-terminal-card border-b border-terminal-border flex items-center justify-between px-4 flex-shrink-0">
      <div className="flex items-center gap-4">
        <span className="text-xs text-terminal-muted font-mono-data">
          <Clock size={12} className="inline mr-1" />
          {time}
        </span>
        <span className={`text-xs font-medium ${statusColor}`}>
          <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1 ${
            marketStatus === '交易中' ? 'bg-terminal-green animate-pulse' : 'bg-terminal-muted'
          }`} />
          A股 {marketStatus}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <button className="text-xs text-terminal-muted hover:text-terminal-text flex items-center gap-1 transition-colors">
          <RefreshCw size={12} />
          刷新
        </button>
        <span className="text-xs text-terminal-muted font-mono-data">
          AI智能投研分析平台 v2.0
        </span>
      </div>
    </header>
  );
}