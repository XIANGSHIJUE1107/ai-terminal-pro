'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Star, TrendingUp, Newspaper, PieChart,
  BarChart3, FileText, Bell, Settings, ChevronLeft, ChevronRight,
  Activity,
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: '首页Dashboard', icon: LayoutDashboard },
  { href: '/watchlist', label: '自选股', icon: Star },
  { href: '/sector', label: '行业板块', icon: PieChart },
  { href: '/fundflow', label: '资金流向', icon: BarChart3 },
  { href: '/news', label: 'AI新闻分析', icon: Newspaper },
  { href: '/review', label: '大盘复盘', icon: Activity },
  { href: '/research', label: 'AI研究报告', icon: FileText },
  { href: '/alerts', label: '预警系统', icon: Bell },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`${
        collapsed ? 'w-16' : 'w-56'
      } bg-terminal-card border-r border-terminal-border flex flex-col transition-all duration-300 relative`}
    >
      {/* Logo */}
      <div className="h-14 flex items-center justify-center border-b border-terminal-border px-3">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-terminal-accent rounded flex items-center justify-center">
              <span className="text-terminal-bg font-bold text-xs">AI</span>
            </div>
            <span className="font-bold text-sm text-terminal-accent whitespace-nowrap">
              投研平台
            </span>
          </div>
        )}
        {collapsed && (
          <div className="w-7 h-7 bg-terminal-accent rounded flex items-center justify-center">
            <span className="text-terminal-bg font-bold text-xs">AI</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 mx-2 rounded-lg mb-0.5 transition-all duration-200 group ${
                isActive
                  ? 'bg-terminal-accent/10 text-terminal-accent border border-terminal-accent/20'
                  : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-hover/30'
              }`}
            >
              <Icon size={18} className={isActive ? 'text-terminal-accent' : ''} />
              {!collapsed && (
                <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="h-10 border-t border-terminal-border flex items-center justify-center hover:bg-terminal-hover/30 transition-colors"
      >
        {collapsed ? <ChevronRight size={16} className="text-terminal-muted" /> : <ChevronLeft size={16} className="text-terminal-muted" />}
      </button>
    </aside>
  );
}