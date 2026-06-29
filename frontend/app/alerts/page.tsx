'use client';

import { useEffect, useState } from 'react';
import { Bell, BellOff, Plus, Trash2, Power, PowerOff } from 'lucide-react';
import { getAlerts, addAlert, toggleAlert, deleteAlert } from '@/lib/api';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({
    symbol: '', name: '', alert_type: 'price',
    condition: '{}', channels: 'web', enabled: true,
  });

  useEffect(() => {
    loadAlerts();
  }, []);

  async function loadAlerts() {
    try {
      const data = await getAlerts();
      setAlerts(data.alerts || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const handleAdd = async () => {
    if (!form.symbol || !form.name) return;
    try {
      await addAlert(form);
      setShowAdd(false);
      await loadAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggle = async (id: number) => {
    try {
      await toggleAlert(id);
      await loadAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteAlert(id);
      await loadAlerts();
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
          <Bell size={20} className="text-terminal-accent" />
          预警系统
        </h1>
        <button onClick={() => setShowAdd(true)} className="btn-accent flex items-center gap-1">
          <Plus size={14} /> 添加预警
        </button>
      </div>

      {/* Add Form */}
      {showAdd && (
        <div className="card-terminal p-4 space-y-3">
          <h3 className="text-sm font-medium">新建预警规则</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <select
              className="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm text-terminal-text"
              value={form.symbol}
              onChange={e => {
                const s = defaultStocks.find(st => st.code === e.target.value);
                setForm({ ...form, symbol: e.target.value, name: s?.name || '' });
              }}
            >
              <option value="">选择股票</option>
              {defaultStocks.map(s => (
                <option key={s.code} value={s.code}>{s.name}</option>
              ))}
            </select>
            <select
              className="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm text-terminal-text"
              value={form.alert_type}
              onChange={e => setForm({ ...form, alert_type: e.target.value })}
            >
              <option value="price">价格突破</option>
              <option value="volume">成交量异常</option>
              <option value="ma">均线突破</option>
              <option value="news">新闻预警</option>
            </select>
            <select
              className="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm text-terminal-text"
              value={form.channels}
              onChange={e => setForm({ ...form, channels: e.target.value })}
            >
              <option value="web">网页通知</option>
              <option value="wecom">企业微信</option>
              <option value="email">邮件</option>
            </select>
            <button onClick={handleAdd} className="btn-blue">确认添加</button>
          </div>
        </div>
      )}

      {/* Alerts List */}
      <div className="card-terminal overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-terminal-border text-xs text-terminal-muted">
              <th className="text-left p-3">标的</th>
              <th className="text-left p-3">类型</th>
              <th className="text-left p-3">通知渠道</th>
              <th className="text-left p-3">创建时间</th>
              <th className="text-center p-3">状态</th>
              <th className="text-center p-3 w-24">操作</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map(a => (
              <tr key={a.id} className="border-b border-terminal-border/50 hover:bg-terminal-hover/20">
                <td className="p-3 text-sm">{a.name}({a.symbol})</td>
                <td className="p-3">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-terminal-accent/10 text-terminal-accent">
                    {a.alert_type === 'price' ? '价格' : a.alert_type === 'volume' ? '成交量' : a.alert_type === 'ma' ? '均线' : '新闻'}
                  </span>
                </td>
                <td className="p-3 text-xs text-terminal-muted">{a.channels}</td>
                <td className="p-3 text-xs text-terminal-muted">{a.created_at}</td>
                <td className="p-3 text-center">
                  <span className={`text-xs ${a.enabled ? 'price-up' : 'text-terminal-muted'}`}>
                    {a.enabled ? '启用' : '停用'}
                  </span>
                </td>
                <td className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <button onClick={() => handleToggle(a.id)} className={a.enabled ? 'price-up' : 'text-terminal-muted'}>
                      {a.enabled ? <Power size={14} /> : <PowerOff size={14} />}
                    </button>
                    <button onClick={() => handleDelete(a.id)} className="text-terminal-muted hover:text-terminal-red">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {alerts.length === 0 && (
          <div className="text-center py-12 text-terminal-muted text-sm">
            暂无预警规则，点击"添加预警"创建
          </div>
        )}
      </div>
    </div>
  );
}
