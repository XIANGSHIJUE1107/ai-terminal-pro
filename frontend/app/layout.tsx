import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/Sidebar';
import { TopBar } from '@/components/TopBar';
import { NewsTicker } from '@/components/NewsTicker';

export const metadata: Metadata = {
  title: 'AI智能投研分析平台 | Professional Edition',
  description: 'Bloomberg + TradingView + Wind 风格的专业AI投研系统',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <TopBar />
          <NewsTicker />
          <main className="flex-1 overflow-y-auto p-4 bg-terminal-bg">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}