# AI 智能投研分析平台 · AI Terminal Pro

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/ECharts-5.5-00D4FF?logo=apache-echarts&logoColor=white" alt="ECharts">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

<p align="center">
  <b>一个面向专业投资者、开源可部署的实时金融终端 + AI 投研分析系统</b><br>
  深度融合市场数据、技术分析、资金流向、新闻舆情与多 Agent 投研决策。
</p>

---

## 设计亮点 ✨

> 为什么我们值得你的 Star

### 1. 彭博 / Wind 级专业终端 UI
- 深色金融风界面，高信息密度、低视觉疲劳
- 卡片式布局，市场概览、持仓、K 线、资金流向、投研分析一屏掌握
- 红涨橙跌的 A 股色彩语义，符合国内交易者直觉
- 响应式滚动，支持多分辨率流畅查看

### 2. 真正的实时多源数据聚合
- 同时接入 **东方财富、新浪财经、同花顺、腾讯财经、AKShare** 等公开数据源
- K 线、分时、资金流向自动多源 failover，单源失效无缝降级
- 个股资金流直接对接东财数据中心 `RPT_DMSK_TS_FUNDFLOWHIS`，非估算、非模拟

### 3. TradingAgents 7-Agent 深度投研框架
独创「指数 / 个股独立分析 + 点击切换」的投研面板：

| Agent | 职责 |
|-------|------|
| 市场概览 | 大盘环境、情绪、成交量解读 |
| 技术分析 | K 线形态、均线、BOLL、支撑位压力位 |
| 舆情监控 | 实时新闻、利好 / 利空事件捕捉 |
| 基本面 | 财务数据、业绩预告、估值分析 |
| 政策与行业 | 产业政策、主题催化、产业链逻辑 |
| 资金流向 | 主力 / 散户净流入、融资融券、大宗交易 |
| 风险监控 | 波动、回撤、黑天鹅信号预警 |
| 多空辩论 | 自动生成 Bull vs Bear 观点 |
| 基金经理决策 | 综合评分 + 加仓 / 减仓 / 持有建议 |

### 4. 交易时段智能刷新
- 上午收盘后 **12:00–12:05** 自动生成午间分析
- 下午收盘后 **15:30–15:35** 自动生成日终分析
- 每日重置触发器，确保不重复、不漏发

### 5. 指数与个股解耦
- 5 大核心指数：上证指数、深证成指、创业板指、沪深 300、科创 50
- 7 只核心持仓股一键切换，独立生成专属投研报告
- 指数面板屏蔽不适用的「主力资金流」，个股面板展示真实主力 / 散户流向

### 6. 鲁棒的后端架构
- 基于 `proxy_server.py` 的轻量级代理服务，绕过浏览器跨域限制
- 内置熔断、限流、缓存与自动重连机制
- 提供 `/api/fundflow/stock` 等 RESTful 数据接口
- 支持 `start_server.py` 自动重启守护

---

## 快速开始 🚀

### 环境要求
- Python 3.10+
- Node.js 18+（如需运行 Next.js 前端）

### 1. 克隆项目

```bash
git clone https://github.com/XIANGSHIJUE1107/ai-terminal-pro.git
cd ai-terminal-pro
```

### 2. 安装 Python 依赖

```bash
pip install -r backend/requirements.txt
```

### 3. 启动数据代理服务

```bash
python proxy_server.py
# 或使用自动重启守护
python start_server.py
```

服务默认运行在：http://127.0.0.1:8080

### 4. 打开终端页面

浏览器访问：

```
http://127.0.0.1:8080/terminal.html
```

### 5. （可选）启动 Next.js 前端

```bash
cd frontend
npm install
npm run dev
```

---

## 项目结构 📁

```
ai-terminal-pro/
├── backend/                  # Python 后端
│   ├── api/                  # RESTful API 路由
│   ├── data_sources/         # 东财、新浪、同花顺等数据源适配器
│   ├── datahub/              # 数据中枢与缓存
│   ├── services/             # 市场数据服务
│   ├── tasks/                # 定时调度器
│   ├── ai/                   # AI 分析与投研生成
│   └── requirements.txt      # Python 依赖
├── frontend/                 # Next.js 前端（现代化版本）
├── terminal.html             # 主终端页面（即开即用）
├── proxy_server.py           # 数据代理与静态服务
├── start_server.py           # 自动重启守护
├── fund-screening-hd/        # 基金筛选模块
└── README.md
```

---

## 核心截图

> 终端主界面：市场概览 + 持仓 + K 线 + 资金流向 + TradingAgents 投研

<p align="center">
  <i>打开 http://127.0.0.1:8080/terminal.html 即可体验</i>
</p>

---

## 数据源说明

本项目所有数据均来自公开金融数据接口，仅供学习研究使用：

- 东方财富（行情、K 线、资金流向、融资融券）
- 新浪财经（实时报价、新闻滚动）
- 同花顺（新闻舆情）
- 腾讯财经（K 线 failover）
- AKShare（A 股 / 全球指数备选数据）

**免责声明**：本软件不构成任何投资建议，市场有风险，投资需谨慎。

---

## 适合谁用

- 个人量化研究者
- 股票 / 基金投资者
- 金融数据分析学习者
- 希望搭建私有投研终端的开发者

---

## 贡献与 Star

如果你认可这个项目，欢迎：

- ⭐ 点击右上角 **Star** 支持我们
- 🍴 Fork 后二次开发
- 💡 提交 Issue 反馈问题或建议
- 🔗 分享给你的投研伙伴

---

## License

[MIT](LICENSE)

---

<p align="center">
  <b>Made with ❤️ for Chinese Investors</b>
</p>
