'use client';

import { Thermometer } from 'lucide-react';

interface SentimentProps {
  sentiment?: {
    sentiment: string;
    score: number;
    up_ratio: number;
    up_sectors: number;
    down_sectors: number;
  };
}

const sentimentConfig: Record<string, { color: string; bg: string; label: string }> = {
  '极度乐观': { color: '#00e676', bg: 'rgba(0,230,118,0.1)', label: '极度乐观' },
  '乐观': { color: '#69f0ae', bg: 'rgba(105,240,174,0.1)', label: '乐观' },
  '中性': { color: '#f0b90b', bg: 'rgba(240,185,11,0.1)', label: '中性' },
  '谨慎': { color: '#ff9800', bg: 'rgba(255,152,0,0.1)', label: '谨慎' },
  '恐慌': { color: '#ff1744', bg: 'rgba(255,23,68,0.1)', label: '恐慌' },
};

export function SentimentGauge({ sentiment }: SentimentProps) {
  const s = sentiment || { sentiment: '中性', score: 50, up_ratio: 50, up_sectors: 0, down_sectors: 0 };
  const config = sentimentConfig[s.sentiment] || sentimentConfig['中性'];

  const rotation = (s.score / 100) * 180 - 90;

  return (
    <div className="card-terminal p-4 flex flex-col items-center">
      <h3 className="text-sm font-medium text-terminal-text mb-3 flex items-center gap-2">
        <Thermometer size={16} className="text-terminal-accent" />
        AI市场温度计
      </h3>

      {/* Gauge */}
      <div className="relative w-40 h-20 overflow-hidden mb-3">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-36 h-36 rounded-full border-[16px] border-terminal-border"
          style={{
            clipPath: 'polygon(0 50%, 100% 50%, 100% 100%, 0 100%)',
          }}
        />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-36 h-36 rounded-full border-[16px] border-transparent"
          style={{
            borderTopColor: 'transparent',
            borderRightColor: 'transparent',
            borderBottomColor: config.color,
            borderLeftColor: config.color,
            clipPath: 'polygon(0 50%, 100% 50%, 100% 100%, 0 100%)',
            opacity: 0.7,
          }}
        />
        <div
          className="absolute bottom-0 left-1/2 w-0.5 h-12 bg-terminal-text origin-bottom transition-transform duration-1000"
          style={{ transform: `translateX(-50%) rotate(${rotation}deg)` }}
        />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-terminal-text" />
      </div>

      {/* Label */}
      <div
        className="px-3 py-1 rounded-full text-sm font-bold"
        style={{ backgroundColor: config.bg, color: config.color }}
      >
        {s.sentiment}
      </div>

      {/* Detail */}
      <div className="grid grid-cols-3 gap-2 mt-3 w-full text-center">
        <div>
          <div className="text-xs text-terminal-muted">上涨板块</div>
          <div className="text-sm font-mono-data price-up">{s.up_sectors}</div>
        </div>
        <div>
          <div className="text-xs text-terminal-muted">下跌板块</div>
          <div className="text-sm font-mono-data price-down">{s.down_sectors}</div>
        </div>
        <div>
          <div className="text-xs text-terminal-muted">上涨比例</div>
          <div className="text-sm font-mono-data text-terminal-accent">{s.up_ratio}%</div>
        </div>
      </div>
    </div>
  );
}