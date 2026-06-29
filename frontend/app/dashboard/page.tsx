'use client';

import { useEffect, useState } from 'react';
import { MarketOverviewCards } from '@/components/MarketOverviewCards';
import { SentimentGauge } from '@/components/SentimentGauge';
import { PortfolioMini } from '@/components/PortfolioMini';
import { NewsFeed } from '@/components/NewsFeed';
import { SectorFlowMini } from '@/components/SectorFlowMini';
import { getDashboardOverview, getMarketSentiment } from '@/lib/api';

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [overview, sent] = await Promise.all([
          getDashboardOverview(),
          getMarketSentiment(),
        ]);
        setData(overview);
        setSentiment(sent);
      } catch (e) {
        console.error('Dashboard load error:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-terminal-muted text-lg">加载中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 市场概览卡片 */}
      <MarketOverviewCards indices={data?.indices} />

      {/* 中部: AI温度计 + 持仓概览 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <SentimentGauge sentiment={sentiment} />
        <div className="lg:col-span-2">
          <PortfolioMini stocks={data?.portfolio} />
        </div>
      </div>

      {/* 下部: 行业资金 + 新闻流 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SectorFlowMini />
        <NewsFeed />
      </div>
    </div>
  );
}