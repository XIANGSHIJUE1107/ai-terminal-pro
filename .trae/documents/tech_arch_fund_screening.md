# 技术架构文档 - 淘金筛网高清重绘版

## 1. 架构设计
```
┌─────────────────────────────────────┐
│         用户界面层 (HTML/CSS)        │
│  ┌───────────────────────────────┐  │
│  │   淘金筛网信息图 (单页应用)     │  │
│  │  - 7个章节模块                 │  │
│  │  - 导出功能按钮                │  │
│  └───────────────────────────────┘  │
├─────────────────────────────────────┤
│         功能层 (JavaScript)         │
│  - PNG导出 (html2canvas)           │
│  - PDF打印 (@media print)          │
│  - 平滑滚动导航                     │
├─────────────────────────────────────┤
│         资源层                       │
│  - Google Fonts (Noto Sans SC)     │
│  - 内联SVG图标                      │
│  - CSS变量主题系统                   │
└─────────────────────────────────────┘
```

## 2. 技术选型
- **前端框架**：纯HTML5 + CSS3 + Vanilla JavaScript（单文件方案）
- **构建工具**：无需构建，直接运行
- **字体方案**：Google Fonts Noto Sans SC (思源黑体) CDN加载
- **图形方案**：CSS绘制 + 内联SVG（无外部图片依赖）
- **导出方案**：
  - PNG：html2canvas库 (CDN)
  - PDF：浏览器原生打印功能 + @media print样式
- **图标**：内联SVG或Unicode符号

## 3. 文件结构
```
fund-screening-hd/
├── index.html          # 主文件（包含全部HTML/CSS/JS）
└── (无其他依赖文件)
```

## 4. CSS架构
```css
/* 设计令牌 */
:root {
  --mc-blue-dark: #003366;      /* 麦肯锡深蓝 */
  --mc-blue: #0066CC;           /* 麦肯锡亮蓝 */
  --mc-blue-light: #E8F4FD;     /* 浅蓝背景 */
  --mc-orange: #FF8C00;         /* 强调橙 */
  --mc-orange-light: #FFF4E6;   /* 浅橙背景 */
  --success: #10B981;           /* 通过绿 */
  --warning: #F59E0B;           /* 观察黄 */
  --danger: #EF4444;            /* 淘汰红 */
  --text-primary: #1F2937;      /* 主文字 */
  --text-secondary: #6B7280;    /* 次要文字 */
  --bg-page: #F9FAFB;           /* 页面背景 */
  --bg-card: #FFFFFF;           /* 卡片背景 */
}
```

## 5. 核心技术实现要点

### 5.1 高清文字渲染
- 使用 `-webkit-font-smoothing: antialiased`
- 字体回退链：'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif
- 行高设置为 1.6-1.8 保证阅读舒适度

### 5.2 打印优化
- `@media print` 隐藏导出按钮
- 设置 `page-break-inside: avoid` 防止表格跨页断裂
- 打印分辨率提示：300dpi+

### 5.3 PNG导出实现
- 引入 html2canvas CDN
- 设置 scale: 2 或 3 保证高清输出
- 处理跨域字体问题（可能需等待字体加载完成）

### 5.4 布局实现
- 主容器 max-width: 1200px, margin: 0 auto
- 各章节使用 `<section>` 语义化标签
- 卡片使用 CSS Grid/Flexbox 布局
- 分隔线使用伪元素或 border 实现

## 6. 数据模型
本页面为静态展示页面，无后端数据交互。所有内容硬编码在HTML中。
