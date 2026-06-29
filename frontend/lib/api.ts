const API_BASE = '/api';

export async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API Error ${res.status}: ${error}`);
  }
  return res.json();
}

// Dashboard
export const getDashboardOverview = () => fetchAPI<any>('/dashboard/overview');
export const getMarketSentiment = () => fetchAPI<any>('/dashboard/sentiment');
export const getPortfolioSummary = () => fetchAPI<any>('/dashboard/portfolio');
export const getMarketIndices = () => fetchAPI<any>('/dashboard/indices');

// Stock
export const getStockKline = (symbol: string, days = 120) =>
  fetchAPI<any>(`/stock/${symbol}/kline?days=${days}`);
export const getStockAnalysis = (symbol: string) =>
  fetchAPI<any>(`/stock/${symbol}/analysis`);
export const getStockSignals = (symbol: string) =>
  fetchAPI<any>(`/stock/${symbol}/signals`);
export const searchStock = (q: string) => fetchAPI<any>(`/stock/search?q=${q}`);

// Watchlist
export const getWatchlist = (market?: string) =>
  fetchAPI<any>(`/watchlist/list${market ? `?market=${market}` : ''}`);
export const addToWatchlist = (data: any) =>
  fetchAPI<any>('/watchlist/add', { method: 'POST', body: JSON.stringify(data) });
export const deleteFromWatchlist = (id: number) =>
  fetchAPI<any>(`/watchlist/${id}`, { method: 'DELETE' });

// News
export const getNewsList = (limit = 50) =>
  fetchAPI<any>(`/news/list?limit=${limit}`);
export const analyzeNews = (newsId: number) =>
  fetchAPI<any>(`/news/analyze/${newsId}`, { method: 'POST' });
export const getNewsSentimentStats = () =>
  fetchAPI<any>('/news/sentiment_stats');

// Sector
export const getSectors = () => fetchAPI<any>('/sector/list');
export const getHotSectors = () => fetchAPI<any>('/sector/hot');
export const getSectorRankings = (sortBy = 'main_net_inflow') =>
  fetchAPI<any>(`/sector/rankings?sort_by=${sortBy}`);

// Fund Flow
export const getFundFlowOverview = () => fetchAPI<any>('/fundflow/overview');
export const getFundFlowTrend = (days = 20) =>
  fetchAPI<any>(`/fundflow/trend?days=${days}`);

// Review
export const getDailyReview = () => fetchAPI<any>('/review/daily');
export const generateReview = () => fetchAPI<any>('/review/generate');

// Research
export const generateReport = (code: string, name: string) =>
  fetchAPI<any>(`/research/generate?target_code=${code}&target_name=${name}`, { method: 'POST' });
export const getReports = () => fetchAPI<any>('/research/list');
export const getReport = (id: number) => fetchAPI<any>(`/research/${id}`);

// Alerts
export const getAlerts = () => fetchAPI<any>('/alerts/list');
export const addAlert = (data: any) =>
  fetchAPI<any>('/alerts/add', { method: 'POST', body: JSON.stringify(data) });
export const toggleAlert = (id: number) =>
  fetchAPI<any>(`/alerts/${id}/toggle`, { method: 'PUT' });
export const deleteAlert = (id: number) =>
  fetchAPI<any>(`/alerts/${id}`, { method: 'DELETE' });