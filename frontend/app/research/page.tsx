'use client';

import { useEffect, useState } from 'react';
import { FileText, Sparkles, Download, Trash2, Search, Plus } from 'lucide-react';
import { getReports, generateReport, getReport, deleteReport } from '@/lib/api';

export default function ResearchPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [viewReport, setViewReport] = useState<any>(null);
  const [form, setForm] = useState({ code: '', name: '', type: 'stock' });
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadReports();
  }, []);

  async function loadReports() {
    try {
      const data = await getReports();
      setReports(data.reports || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const handleGenerate = async () => {
    if (!form.code || !form.name) return;
    setGenerating(true);
    try {
      await generateReport(form.code, form.name);
      setShowModal(false);
      await loadReports();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const handleView = async (id: number) => {
    try {
      const data = await getReport(id);
      setViewReport(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteReport(id);
      await loadReports();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="animate-pulse text-terminal-muted">加载中...</div></div>;
  }

  const defaultStocks = [
    { code: '600487', name: '亨通光电' },
    { code: '002475', name: '立讯精密' },
    { code: '002384', name: '东山精密' },
    { code: '000988', name: '华工科技' },
    { code: '600459', name: '贵研铂业' },
    { code: '603211', name: '晋拓股份' },
    { code: '600206', name: '有研新材' },
    { code: '000636', name: '风华高科' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <FileText size={20} className="text-terminal-accent" />
          AI研究报告中心
        </h1>
        <button onClick={() => setShowModal(true)} className="btn-accent flex items-center gap-1">
          <Plus size={14} /> 生成新报告
        </button>
      </div>

      {/* Generate Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card-terminal p-6 w-full max-w-md space-y-4">
            <h3 className="text-lg font-bold">生成AI研究报告</h3>
            <div>
              <label className="text-xs text-terminal-muted block mb-1">选择标的</label>
              <select
                className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-sm text-terminal-text"
                value={form.code}
                onChange={e => {
                  const stock = defaultStocks.find(s => s.code === e.target.value);
                  setForm({ ...form, code: e.target.value, name: stock?.name || '' });
                }}
              >
                <option value="">-- 选择股票 --</option>
                {defaultStocks.map(s => (
                  <option key={s.code} value={s.code}>{s.name}({s.code})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-terminal-muted block mb-1">报告类型</label>
              <select
                className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-sm text-terminal-text"
                value={form.type}
                onChange={e => setForm({ ...form, type: e.target.value })}
              >
                <option value="stock">个股研究</option>
                <option value="industry">行业研究</option>
                <option value="theme">主题研究</option>
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-sm text-terminal-muted border border-terminal-border rounded hover:text-terminal-text">
                取消
              </button>
              <button onClick={handleGenerate} disabled={generating} className="btn-accent">
                {generating ? '生成中...' : '开始生成'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Report Modal */}
      {viewReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card-terminal p-6 w-full max-w-3xl max-h-[80vh] overflow-y-auto space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold">{viewReport.title}</h3>
              <button onClick={() => setViewReport(null)} className="text-terminal-muted hover:text-terminal-text">关闭</button>
            </div>
            <div className="text-xs text-terminal-muted">
              {viewReport.created_at} | AI: {viewReport.ai_model}
            </div>
            <div className="text-sm text-terminal-text leading-relaxed whitespace-pre-wrap border-t border-terminal-border pt-3">
              {viewReport.content}
            </div>
          </div>
        </div>
      )}

      {/* Reports List */}
      <div className="card-terminal overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-terminal-border text-xs text-terminal-muted">
              <th className="text-left p-3">标题</th>
              <th className="text-left p-3">标的</th>
              <th className="text-left p-3">类型</th>
              <th className="text-left p-3">AI模型</th>
              <th className="text-left p-3">生成时间</th>
              <th className="text-center p-3 w-24">操作</th>
            </tr>
          </thead>
          <tbody>
            {reports.map(r => (
              <tr key={r.id} className="border-b border-terminal-border/50 hover:bg-terminal-hover/20">
                <td className="p-3 text-sm text-terminal-text">{r.title}</td>
                <td className="p-3 text-sm">{r.target_name}({r.target_code})</td>
                <td className="p-3">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-terminal-accent/10 text-terminal-accent">
                    {r.report_type === 'stock' ? '个股' : r.report_type === 'industry' ? '行业' : '主题'}
                  </span>
                </td>
                <td className="p-3 text-xs text-terminal-muted">{r.ai_model}</td>
                <td className="p-3 text-xs text-terminal-muted">{r.created_at}</td>
                <td className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <button onClick={() => handleView(r.id)} className="text-terminal-accent-blue hover:text-terminal-accent">
                      <Search size={14} />
                    </button>
                    <button onClick={() => handleDelete(r.id)} className="text-terminal-muted hover:text-terminal-red">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {reports.length === 0 && (
          <div className="text-center py-12 text-terminal-muted text-sm">
            暂无研究报告，点击"生成新报告"开始
          </div>
        )}
      </div>
    </div>
  );
}
