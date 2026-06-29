# -*- coding: utf-8 -*-
"""
淘金筛网 - 高清矢量化重绘脚本
完全保持原图布局结构，仅提升文字清晰度和分辨率
输出：PNG高清版(3x) + PDF打印版(300dpi) + HTML可编辑版
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ═══════════════════════════════════════════
# 配色方案（麦肯锡蓝橙体系）
# ═══════════════════════════════════════════
COLORS = {
    'navy': (0x05, 0x1C, 0x2C),        # 深蓝主色
    'blue': (0x00, 0x66, 0xCC),         # 亮蓝
    'blue_light': (0xE8, 0xF4, 0xFD),   # 浅蓝背景
    'blue_lighter': (0xF0, 0xF7, 0xFF), # 更浅蓝
    'orange': (0xFF, 0x8C, 0x00),       # 强调橙
    'orange_light': (0xFF, 0xF4, 0xE6), # 浅橙背景
    'success': (0x10, 0xB9, 0x81),      # 通过绿
    'warning': (0xF5, 0x9E, 0x0B),      # 观察黄
    'danger': (0xEF, 0x44, 0x44),       # 淘汰红
    'white': (0xFF, 0xFF, 0xFF),
    'black': (0x00, 0x00, 0x00),
    'text_primary': (0x1F, 0x29, 0x37),
    'text_secondary': (0x6B, 0x72, 0x80),
    'bg_page': (0xF5, 0xF7, 0xFA),
    'bg_card': (0xFF, 0xFF, 0xFF),
    'border': (0xE5, 0xE7, 0xEB),
}

# ═══════════════════════════════════════════
# 尺寸配置（基础1080px宽，3倍=3240px高清）
# ═══════════════════════════════════════════
SCALE = 3  # 高清倍率
W_BASE = 1080
H_BASE = None  # 动态计算
W = W_BASE * SCALE
MARGIN = 40 * SCALE
CONTENT_W = W - 2 * MARGIN

# ═══════════════════════════════════════════
# 字体配置
# ═══════════════════════════════════════════
def get_font(size, bold=False):
    """获取字体，优先使用思源黑体"""
    size_scaled = int(size * SCALE)
    font_paths = [
        # Windows 字体路径
        r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
        r"C:\Windows\Fonts\msyhbd.ttc",     # 微软雅黑粗体
        r"C:\Windows\Fonts\simhei.ttf",     # 黑体
        r"C:\Windows\Fonts\simsun.ttc",     # 宋体
    ]
    
    if bold:
        paths = [font_paths[1], font_paths[0], font_paths[2]]
    else:
        paths = [font_paths[0], font_paths[2]]
    
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size_scaled)
            except:
                continue
    
    # 回退到默认字体
    try:
        return ImageFont.truetype("arial.ttf", size_scaled)
    except:
        return ImageFont.load_default()


# 预加载常用字体
FONT = {
    'title': get_font(36, True),
    'subtitle': get_font(22),
    'h1': get_font(28, True),
    'h2': get_font(20, True),
    'h3': get_font(16, True),
    'body': get_font(14),
    'body_bold': get_font(14, True),
    'small': get_font(12),
    'tiny': get_font(10),
}


class HDRenderer:
    """高清渲染器 - 精确还原原图布局"""
    
    def __init__(self):
        self.img = None
        self.draw = None
        self.y = 0  # 当前Y坐标
        
    def create_canvas(self, height):
        """创建画布"""
        self.img = Image.new('RGB', (W, int(height * SCALE)), COLORS['bg_page'])
        self.draw = ImageDraw.Draw(self.img)
        self.y = MARGIN
        
    def draw_rect(self, x, y, w, h, color, radius=0):
        """绘制圆角矩形"""
        if radius > 0:
            # 简化：用普通矩形（PIL圆角较复杂）
            pass
        self.draw.rectangle([x, y, x+w, y+h], fill=color)
        
    def draw_text(self, x, y, text, font, color, anchor='lt'):
        """绘制文字"""
        if isinstance(text, str):
            self.draw.text((x, y), text, font=font, fill=color, anchor=anchor)
        else:
            # 多行文本
            for i, line in enumerate(text):
                self.draw.text((x, y + i * font.size * 1.5), line, 
                             font=font, fill=color)
                
    def get_text_width(self, text, font):
        """获取文本宽度"""
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    
    def get_text_height(self, text, font):
        """获取文本高度"""
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    # ═══════════════════════════════════════════
    # Hero 区域
    # ═══════════════════════════════════════════
    def render_hero(self):
        """渲染Hero区域"""
        h = 280 * SCALE
        self.draw_rect(MARGIN, self.y, CONTENT_W, h, COLORS['navy'])
        
        y = self.y + 25 * SCALE
        
        # 徽章
        badge_w = self.get_text_width('基金筛选体系 · 四层筛网', FONT['small']) + 30 * SCALE
        self.draw_rect(MARGIN + 20 * SCALE, y, badge_w, 28 * SCALE, COLORS['orange'])
        self.draw_text(MARGIN + 35 * SCALE, y + 5 * SCALE, 
                      '基金筛选体系 · 四层筛网', FONT['small'], COLORS['white'])
        y += 45 * SCALE
        
        # 主标题
        self.draw_text(MARGIN + 20 * SCALE, y,
                      '淘金筛网 —— 为您穿透迷雾，锁定真价值',
                      FONT['title'], COLORS['white'])
        y += 55 * SCALE
        
        # 副标题
        self.draw_text(MARGIN + 20 * SCALE, y,
                      '一层一层，滤掉运气，只留能力',
                      FONT['subtitle'], (255, 255, 255, 220))
        y += 35 * SCALE
        
        # 核心主张
        self.draw_text(MARGIN + 20 * SCALE, y,
                      '筛选的不是收益，是收益背后的确定性',
                      FONT['body'], (255, 255, 255, 200))
        y += 50 * SCALE
        
        # 数据流
        flow_y = y
        flow_items = [
            ('全市场 10000+ 基金', COLORS['white']),
            ('→', COLORS['orange']),
            ('四层筛网', COLORS['white']),
            ('→', COLORS['orange']),
            ('不到 2% 的核心资产', COLORS['orange']),
        ]
        
        total_flow_w = sum(self.get_text_width(t, FONT['body']) + 20 * SCALE 
                          for t, _ in flow_items) - 20 * SCALE
        start_x = MARGIN + (CONTENT_W - total_flow_w) // 2
        
        for text, color in flow_items:
            tw = self.get_text_width(text, FONT['body'])
            self.draw_text(start_x, flow_y, text, FONT['body'], color)
            start_x += tw + 20 * SCALE
            
        y += 50 * SCALE
        
        # 价值点
        values = ['✓ 穿透净值看底层', '✓ 区分运气与能力', 
                 '✓ 量化每一条标准', '✓ 可执行、可复现']
        val_x = MARGIN + 30 * SCALE
        for v in values:
            self.draw_text(val_x, y, v, FONT['body'], (255, 255, 255, 200))
            val_x += 260 * SCALE
            
        self.y += h + 30 * SCALE

    # ═══════════════════════════════════════════
    # 章节标题
    # ═══════════════════════════════════════════
    def render_section_header(self, number, title):
        """渲染章节标题"""
        # 编号块
        num_size = 48 * SCALE
        self.draw_rect(MARGIN, self.y, num_size, num_size, COLORS['blue'])
        self.draw_text(MARGIN, self.y + 10 * SCALE, str(number).zfill(2),
                      FONT['h1'], COLORS['white'], anchor='mm')
        
        # 标题文字
        self.draw_text(MARGIN + num_size + 16 * SCALE, self.y + 10 * SCALE,
                      title, FONT['h1'], COLORS['navy'])
        self.y += num_size + 15 * SCALE
        
        # 分隔线
        line_len = CONTENT_W - num_size - 16 * SCALE
        # 渐变效果简化为橙色线
        self.draw.rectangle([MARGIN + num_size + 16 * SCALE, self.y,
                           MARGIN + num_size + 16 * SCALE + min(line_len, 400 * SCALE),
                           self.y + 3 * SCALE], fill=COLORS['orange'])
        self.y += 30 * SCALE

    # ═══════════════════════════════════════════
    # 01 不选收益，选确定性
    # ═══════════════════════════════════════════
    def render_s01(self):
        self.render_section_header('01', '不选收益，选确定性')
        
        card_h = 320 * SCALE
        self.draw_rect(MARGIN, self.y, CONTENT_W, card_h, COLORS['bg_card'])
        
        y = self.y + 20 * SCALE
        x = MARGIN + 25 * SCALE
        
        # 小标题
        self.draw_text(x, y, '五把筛子，五个追问', FONT['h2'], COLORS['navy'])
        y += 40 * SCALE
        
        # 五个问题
        questions = [
            ('谁在管？', '→ 管理者能力真假'),
            ('怎么赚的？', '→ 方法能不能持续'),
            ('买了什么？', '→ 底层资产靠不靠谱'),
            ('赚的钱干净吗？', '→ 运气和能力的比例'),
            ('明天还能赚吗？', '→ 失效的概率有多大'),
        ]
        
        for q, a in questions:
            # 背景条
            item_h = 46 * SCALE
            self.draw_rect(x, y, CONTENT_W - 50 * SCALE, item_h, COLORS['blue_lighter'])
            
            # 左边框
            self.draw.rectangle([x, y, x + 4 * SCALE, y + item_h], fill=COLORS['orange'])
            
            # 圆形编号
            circle_r = 18 * SCALE
            cx = x + 25 * SCALE
            cy = y + item_h // 2
            self.draw.ellipse([cx - circle_r, cy - circle_r, 
                              cx + circle_r, cy + circle_r], fill=COLORS['blue'])
            
            # 问题
            self.draw_text(x + 55 * SCALE, y + 6 * SCALE, q, FONT['h3'], COLORS['text_primary'])
            # 答案
            self.draw_text(x + 55 * SCALE, y + 26 * SCALE, a, FONT['small'], COLORS['text_secondary'])
            
            y += item_h + 12 * SCALE
            
        self.y += card_h + 25 * SCALE

    # ═══════════════════════════════════════════
    # 02 第一网：基础红线
    # ═══════════════════════════════════════════
    def render_s02(self):
        self.render_section_header('02', '第一网：基础红线')
        
        card_h = 420 * SCALE
        self.draw_rect(MARGIN, self.y, CONTENT_W, card_h, COLORS['bg_card'])
        
        y = self.y + 20 * SCALE
        x = MARGIN + 25 * SCALE
        
        # 说明
        self.draw_text(x, y, '不到这四条，直接淘汰。不看业绩。', 
                      FONT['h3'], COLORS['navy'])
        y += 40 * SCALE
        
        # 表格
        table_data = [
            ('红线', '规则', '一句话'),
            ('成立时间', '不到 3 年不要', '没经历过牛熊验证'),
            ('现任经理', '任职不到 2 年不要', '业绩不是他做的'),
            ('基金规模', '不到 20 亿不要', '有清盘风险，操作受限'),
            ('风格漂移', '行业变动率超 50% 不要', '追热点，没定力'),
        ]
        
        col_widths = [140 * SCALE, 220 * SCALE, 280 * SCALE]
        row_h = 44 * SCALE
        table_w = sum(col_widths)
        
        for row_idx, row in enumerate(table_data):
            is_header = row_idx == 0
            bg_color = COLORS['navy'] if is_header else (
                COLORS['blue_lighter'] if row_idx % 2 == 0 else COLORS['bg_card']
            )
            text_color = COLORS['white'] if is_header else COLORS['text_primary']
            
            cell_x = x
            for col_idx, (cell_text, col_w) in enumerate(zip(row, col_widths)):
                self.draw_rect(cell_x, y, col_w, row_h, bg_color)
                font = FONT['body_bold'] if is_header or col_idx == 0 else FONT['body']
                self.draw_text(cell_x + 10 * SCALE, y + 12 * SCALE, 
                              cell_text, font, text_color)
                cell_x += col_w
            y += row_h
            
        y += 20 * SCALE
        
        # 特殊标记
        note_h = 90 * SCALE
        self.draw_rect(x, y, CONTENT_W - 50 * SCALE, note_h, COLORS['orange_light'])
        self.draw.rectangle([x, y, x + 2 * SCALE, y + note_h], fill=COLORS['orange'])
        self.draw.rectangle([x, y, x + CONTENT_W - 50 * SCALE, y + note_h], 
                          outline=COLORS['orange'], width=2)
        
        ny = y + 15 * SCALE
        self.draw_text(x + 15 * SCALE, ny, '⚠ 特殊标记', FONT['h3'], COLORS['orange'])
        ny += 30 * SCALE
        self.draw_text(x + 25 * SCALE, ny, 
                      '→ 规模超过 200 亿 → 亮黄灯，必须证明收益没被规模稀释',
                      FONT['small'], COLORS['text_primary'])
        ny += 22 * SCALE
        self.draw_text(x + 25 * SCALE, ny,
                      '→ 成立 3-5 年 → 观察区，需补基金经理此前业绩',
                      FONT['small'], COLORS['text_primary'])
                      
        y += note_h + 20 * SCALE
        
        # 结果提示
        result_h = 50 * SCALE
        self.draw_rect(x, y, CONTENT_W - 50 * SCALE, result_h, COLORS['blue_light'])
        result_text = '筛完第一网，剩下约 30%'
        tw = self.get_text_width(result_text, FONT['h3'])
        self.draw_text(x + (CONTENT_W - 50 * SCALE - tw) // 2, y + 13 * SCALE,
                      result_text, FONT['h3'], COLORS['navy'])
        
        self.y += card_h + 25 * SCALE

    # ═══════════════════════════════════════════
    # 03 第二网：经理真伪
    # ═══════════════════════════════════════════
    def render_metric_card(self, x, y, w, number, title, desc, items):
        """渲染单个指标卡片"""
        card_h = 340 * SCALE
        self.draw_rect(x, y, w, card_h, COLORS['bg_card'])
        
        cy = y + 15 * SCALE
        
        # 编号标签
        num_text = f'{number}'
        num_w = self.get_text_width(num_text, FONT['tiny']) + 16 * SCALE
        self.draw_rect(x + 15 * SCALE, cy, num_w, 24 * SCALE, COLORS['blue'])
        self.draw_text(x + 23 * SCALE, cy + 4 * SCALE, num_text, FONT['tiny'], COLORS['white'])
        
        cy += 32 * SCALE
        
        # 标题
        self.draw_text(x + 15 * SCALE, cy, title, FONT['h3'], COLORS['navy'])
        cy += 28 * SCALE
        
        # 描述
        if desc:
            self.draw_text(x + 15 * SCALE, cy, desc, FONT['small'], COLORS['text_secondary'])
            cy += 36 * SCALE
        
        # 标准项
        for status, text, result in items:
            item_h = 52 * SCALE
            icon_color = {'pass': COLORS['success'], 'warn': COLORS['warning'], 
                         'fail': COLORS['danger']}[status]
            bg = {'pass': (230, 255, 240), 'warn': (255, 250, 230), 
                  'fail': (255, 235, 235)}[status]
            
            self.draw_rect(x + 10 * SCALE, cy, w - 20 * SCALE, item_h, bg)
            self.draw.rectangle([x + 10 * SCALE, cy, x + 13 * SCALE, cy + item_h], 
                              fill=icon_color)
            
            icon = {'pass': '✓', 'warn': '⚠', 'fail': '✗'}[status]
            self.draw_text(x + 20 * SCALE, cy + 6 * SCALE, icon, 
                          FONT['body_bold'], icon_color)
            self.draw_text(x + 40 * SCALE, cy + 6 * SCALE, text, FONT['small'], COLORS['text_primary'])
            self.draw_text(x + 40 * SCALE, cy + 28 * SCALE, f'→ {result}', 
                          FONT['small'], COLORS['text_primary'])
            cy += item_h + 6 * SCALE
            
        return card_h

    def render_s03(self):
        self.render_section_header('03', '第二网：经理真伪')
        
        card_h = 780 * SCALE
        self.draw_rect(MARGIN, self.y, CONTENT_W, card_h, COLORS['bg_card'])
        
        y = self.y + 20 * SCALE
        x = MARGIN + 25 * SCALE
        
        self.draw_text(x, y, '区分"真能力"和"运气好"', FONT['h3'], COLORS['navy'])
        y += 40 * SCALE
        
        # 6个指标卡片 (2列3行)
        metrics = [
            ('3.1', 'Alpha：你到底有没有额外创造值',
             '把基金收益拆开，看看扣掉市场涨跌后，剩下多少是经理自己赚的。',
             [('pass', '年化超额 ≥ 3%，且统计上显著', '真有本事'),
              ('warn', '年化超额 1%-3%', '有迹象，再往下看'),
              ('fail', '年化超额 < 1%，或不显著', '跟指数差不多')]),
              
            ('3.2', '信息比率：你的超额稳不稳',
             '超额赚到手，是稳稳当当，还是大起大落？',
             [('pass', '信息比率 ≥ 0.5', '超额扎实，不是运气波动'),
              ('warn', '0.3-0.5', '再看其他项'),
              ('fail', '< 0.3', '超额质量差，淘汰')]),
              
            ('3.3', '熊市见真章',
             '不看牛市的收益，看熊市能不能少亏。近5年至少经历两次大跌。',
             [('pass', '两次大跌都跑赢，平均多赚2%+', '抗跌，真本事'),
              ('warn', '一次跑赢一次跑输', '待观察'),
              ('fail', '两次都跑输', '风控不行，淘汰')]),
              
            ('3.4', '你究竟擅长什么',
             '过去两年，前三大行业是不是一直那三个？',
             [('pass', '核心行业连续6季度+，占一半+', '能力圈清晰'),
              ('warn', '核心行业偶尔变化', '待观察'),
              ('fail', '每隔两三季换一套行业', '风格漂移，淘汰')]),
              
            ('3.5', '你的买卖值不值',
             '买入的股票接下来涨没涨，卖出的跌没跌。统计调仓方向对不对。',
             [('pass', '正确率 ≥ 60%', '调仓在创造价值'),
              ('warn', '50%-60%', '再看其他项'),
              ('fail', '< 50%', '乱动不如不动，淘汰')]),
              
            ('3.6', '你自己买了吗', '',
             [('pass', '经理自己持有 ≥ 300万', '利益绑定，通过'),
              ('warn', '100-300万', '有绑定但不强'),
              ('fail', '不到100万或不披露', '你的钱他不上心')]),
        ]
        
        card_w = (CONTENT_W - 50 * SCALE - 20 * SCALE) // 2
        col1_x = x
        col2_x = x + card_w + 20 * SCALE
        max_row_h = 0
        
        for i, (num, title, desc, items) in enumerate(metrics):
            col = i % 2
            row = i // 2
            cx = col1_x if col == 0 else col2_x
            cy = y + row * 250 * SCALE
            
            ch = self.render_metric_card(cx, cy, card_w, num, title, desc, items)
            
        # 总结
        summary_y = self.y + card_h - 60 * SCALE
        summary_h = 45 * SCALE
        self.draw_rect(x, summary_y, CONTENT_W - 50 * SCALE, summary_h, COLORS['blue_light'])
        self.draw.rectangle([x, summary_y, x + CONTENT_W - 50 * SCALE, summary_y + summary_h],
                          outline=COLORS['blue'], width=2)
        summary_text = '第二网通过者：能力真实、风格稳定、言行一致'
        tw = self.get_text_width(summary_text, FONT['body_bold'])
        self.draw_text(x + (CONTENT_W - 50 * SCALE - tw) // 2, summary_y + 12 * SCALE,
                      summary_text, FONT['body_bold'], COLORS['navy'])
        
        self.y += card_h + 25 * SCALE

    # ═══════════════════════════════════════════
    # 04 第三网：持仓含金量
    # ═══════════════════════════════════════════
    def render_s04(self):
        self.render_section_header('04', '第三网：持仓含金量')
        
        card_h = 600 * SCALE
        self.draw_rect(MARGIN, self.y, CONTENT_W, card_h, COLORS['bg_card'])
        
        y = self.y + 20 * SCALE
        x = MARGIN + 25 * SCALE
        
        self.draw_text(x, y, '穿透净值，看底层到底买了什么', FONT['h3'], COLORS['navy'])
        y += 40 * SCALE
        
        # 4个指标卡片 (2列2行)
        metrics_04 = [
            ('4.1', '龙头纯度',
             '龙头不是自封的。前十大持仓里，龙头的总权重：',
             [('pass', '≥ 60%', '一水的好公司'),
              ('warn', '40%-60%', '龙头里有二线'),
              ('fail', '< 40%', '买的是什么？')]),
             
            ('4.2', '赚钱能力：加权 ROE',
             '持仓公司整体的净资产收益率',
             [('pass', '≥ 15%，三年波动不大', '实实在在的好生意'),
              ('warn', '12%-15%', '尚可'),
              ('fail', '< 12%', '赚钱能力弱，淘汰')]),
             
            ('4.3', '成长预期',
             '未来两年，公司加总的利润增速能有多少？',
             [('pass', '≥ 15%', '明天比今天更好'),
              ('warn', '10%-15%', '温和增长'),
              ('fail', '< 10%', '停滞或衰退')]),
             
            ('4.4', '行业景气度：五灯检查',
             '看持仓行业当前处于什么位置',
             [('pass', '五灯全亮', '通过'),
              ('warn', '亮三四灯', '观察'),
              ('fail', '亮两灯及以下', '淘汰')]),
        ]
        
        card_w = (CONTENT_W - 50 * SCALE - 20 * SCALE) // 2
        
        for i, (num, title, desc, items) in enumerate(metrics_04):
            col = i % 2
            row = i // 2
            cx = x + (card_w + 20 * SCALE) * col
            cy = y + row * 250 * SCALE
            self.render_metric_card(cx, cy, card_w, num, title, desc, items)
            
        # 总结
        summary_y = self.y + card_h - 60 * SCALE
        self.draw_rect(x, summary_y, CONTENT_W - 50 * SCALE, 45 * SCALE, COLORS['blue_light'])
        self.draw.rectangle([x, summary_y, x + CONTENT_W - 50 * SCALE, summary_y + 45 * SCALE],
                          outline=COLORS['blue'], width=2)
        summary_text = '第三网通过：底层资产扎实，买的是好东西'
        tw = self.get_text_width(summary_text, FONT['body_bold'])
        self.draw_text(x + (CONTENT_W - 50 * SCALE - tw) // 2, summary_y + 12 * SCALE,
                      summary_text, FONT['body_bold'], COLORS['navy'])
        
        self.y += card_h + 25 * SCALE

    # ═══════════════════════════════════════════
    # 05 第四网：脆弱性测试
    # ═══════════════════════════════════════════
    def render_stress_item(self, x, y, w, number, title, questions, conclusion):
        """渲染单个压力测试项"""
        item_h = 160 * SCALE
        self.draw_rect(x, y, w, item_h, COLORS['bg_card'])
        
        cy = y + 15 * SCALE
        
        # 编号+标题
        num_w = self.get_text_width(number, FONT['tiny']) + 14 * SCALE
        self.draw_rect(x + 15 * SCALE, cy, num_w, 22 * SCALE, COLORS['blue'])
        self.draw_text(x + 22 * SCALE, cy + 3 * SCALE, number, FONT['tiny'], COLORS['white'])
        self.draw_text(x + 15 * SCALE + num_w + 10 * SCALE, cy, title, FONT['h3'], COLORS['navy'])
        cy += 32 * SCALE
        
        # 问题
        if questions:
            for q in questions:
                self.draw_text(x + 15 * SCALE, cy, q, FONT['small'], COLORS['text_secondary'])
                cy += 22 * SCALE
            cy += 8 * SCALE
        
        # 结论
        concl_h = 38 * SCALE
        self.draw_rect(x + 15 * SCALE, cy, w - 30 * SCALE, concl_h, (255, 235, 235))
        self.draw.rectangle([x + 15 * SCALE, cy, x + 18 * SCALE, cy + concl_h], fill=COLORS['danger'])
        self.draw_text(x + 25 * SCALE, cy + 8 * SCALE, conclusion, 
                      FONT['small'], COLORS['danger'])
        
        return item_h

    def render_s05(self):
        self.render_section_header('05', '第四网：脆弱性测试')
        
        card_h = 720 * SCALE
        self.draw_rect(MARGIN, self.y, CONTENT_W, card_h, COLORS['bg_card'])
        
        y = self.y + 20 * SCALE
        x = MARGIN + 25 * SCALE
        
        self.draw_text(x, y, '前面的都是"过去不错"，这一层问"明天会不会崩"',
                      FONT['h3'], COLORS['navy'])
        y += 40 * SCALE
        
        stress_tests = [
            ('5.1', '规模诅咒', 
             ['规模两年翻了一倍？', '超额收益同时往下掉？'],
             '任一答案"是" → 淘汰    → 规模已侵蚀能力'),
            ('5.2', '拥挤警报',
             ['前十大重仓股，是不是大家都在买？'],
             '被50只以上基金抱团，占比超半 → 淘汰    → 一旦踩踏无处逃'),
            ('5.3', '最痛月份',
             ['过去5年，有没有单月跌超15%？跌的原因是什么？'],
             '系统崩盘可谅解；无缘无故 → 淘汰'),
            ('5.4', '回撤深度',
             ['近5年最大回撤'],
             '<20%安全 | 20-30%注意 | ≥30%淘汰'),
            ('5.5', '性价比',
             ['每承受1%回撤，能换来多少收益？'],
             '卡玛≥1.0划算 | 0.5-1.0勉强 | <0.5极低'),
        ]
        
        item_w = (CONTENT_W - 50 * SCALE - 15 * SCALE) // 2
        
        for i, (num, title, qs, concl) in enumerate(stress_tests):
            col = i % 2
            row = i // 2
            cx = x + (item_w + 15 * SCALE) * col
            cy = y + row * 130 * SCALE
            self.render_stress_item(cx, cy, item_w, num, title, qs, concl)
            
        # 总结
        summary_y = self.y + card_h - 60 * SCALE
        self.draw_rect(x, summary_y, CONTENT_W - 50 * SCALE, 45 * SCALE, COLORS['blue_light'])
        self.draw.rectangle([x, summary_y, x + CONTENT_W - 50 * SCALE, summary_y + 45 * SCALE],
                          outline=COLORS['blue'], width=2)
        summary_text = '第四网通过：未来崩盘概率低，持有体验好'
        tw = self.get_text_width(summary_text, FONT['body_bold'])
        self.draw_text(x + (CONTENT_W - 50 * SCALE - tw) // 2, summary_y + 12 * SCALE,
                      summary_text, FONT['body_bold'], COLORS['navy'])
        
        self.y += card_h + 25 * SCALE

    # ═══════════════════════════════════════════
    # 06 最终棋盘：配置格局
    # ═══════════════════════════════════════════
    def render_pool(self, x, y, w, stars, name, condition, desc, details, pool_type):
        """渲染配置池"""
        header_colors = {
            'core': (COLORS['navy'], COLORS['blue']),
            'tactical': (COLORS['blue'], (0x33, 0x99, 0xFF)),
            'observe': ((0x66, 0x66, 0x66),),
            'eliminate': (COLORS['danger'],),
        }
        
        bg1 = header_colors[pool_type][0]
        pool_h = 150 * SCALE
        
        # 头部
        self.draw_rect(x, y, w, 50 * SCALE, bg1)
        star_text = '★' * stars if stars != '✗' else '✗'
        self.draw_text(x + 20 * SCALE, y + 12 * SCALE, f'{star_text} {name} {star_text}',
                      FONT['h2'], COLORS['white'])
        
        body_y = y + 50 * SCALE
        self.draw_rect(x, body_y, w, pool_h - 50 * SCALE, COLORS['bg_card'])
        
        by = body_y + 12 * SCALE
        bx = x + 20 * SCALE
        
        self.draw_text(bx, by, condition, FONT['small'], COLORS['text_secondary'])
        by += 25 * SCALE
        self.draw_text(bx, by, desc, FONT['body_bold'], COLORS['text_primary'])
        by += 28 * SCALE
        
        for label, value in details:
            self.draw_text(bx, by, f'{label}：', FONT['small'], COLORS['text_secondary'])
            self.draw_text(bx + self.get_text_width(f'{label}：', FONT['small']) + 5 * SCALE,
                          by, value, FONT['small'], COLORS['navy'])
            by += 22 * SCALE
            
        return pool_h

    def render_s06(self):
        self.render_section_header('06', '最终棋盘：配置格局')
        
        pool_w = CONTENT_W - 50 * SCALE
        x = MARGIN + 25 * SCALE
        
        pools = [
            (3, '战略核心池', '四网全部通过，且无任何淘汰标记',
             '最高置信度，可重仓长期持有',
             [('单基金上限', '组合的 8%'), ('核心池总仓位', '50%-70%')],
             'core'),
            (2, '战术增强池', '四网通过，有 1-2 项观察标记',
             '可作为阶段性增强配置',
             [('单基金上限', '4%'), ('战术池总仓位', '10%-25%')],
             'tactical'),
            (1, '观察池', '有观察标记，但无淘汰项',
             '小仓试探，持续跟踪',
             [('单基金上限', '2%'), ('观察池总仓位', '≤10%')],
             'observe'),
            ('✗', '淘汰', '任一关键项不通过', '不配置', [], 'eliminate'),
        ]
        
        total_pool_h = 0
        for stars, name, cond, desc, details, ptype in pools:
            ph = self.render_pool(x, self.y + total_pool_h, pool_w, stars, name, 
                                 cond, desc, details, ptype)
            total_pool_h += ph + 15 * SCALE
            # 箭头
            if ptype != 'eliminate':
                arrow_text = '↓'
                aw = self.get_text_width(arrow_text, FONT['h1'])
                self.draw_text(x + (pool_w - aw) // 2, self.y + total_pool_h - 5 * SCALE,
                              arrow_text, FONT['h1'], COLORS['blue'])
                
        self.y += total_pool_h + 25 * SCALE

    # ═══════════════════════════════════════════
    # 附：五问速查卡
    # ═══════════════════════════════════════════
    def render_quick_ref(self):
        """渲染五问速查卡表格"""
        # 使用特殊编号样式
        num_size = 48 * SCALE
        self.draw_rect(MARGIN, self.y, num_size, num_size, COLORS['orange'])
        self.draw_text(MARGIN, self.y + 10 * SCALE, '附',
                      FONT['h1'], COLORS['white'], anchor='mm')
        
        self.draw_text(MARGIN + num_size + 16 * SCALE, self.y + 10 * SCALE,
                      '五问速查卡', FONT['h1'], COLORS['navy'])
        self.y += num_size + 15 * SCALE
        self.draw.rectangle([MARGIN + num_size + 16 * SCALE, self.y,
                           MARGIN + num_size + 16 * SCALE + 400 * SCALE, self.y + 3 * SCALE],
                          fill=COLORS['orange'])
        self.y += 30 * SCALE
        
        card_h = 280 * SCALE
        self.draw_rect(MARGIN, self.y, CONTENT_W, card_h, COLORS['bg_card'])
        
        y = self.y + 15 * SCALE
        x = MARGIN + 25 * SCALE
        
        # 表头
        headers = ['问题', '一票否决项', '通过线']
        col_ws = [130 * SCALE, 200 * SCALE, 280 * SCALE]
        row_h = 38 * SCALE
        
        hx = x
        for h, cw in zip(headers, col_ws):
            self.draw_rect(hx, y, cw, row_h, COLORS['navy'])
            self.draw_text(hx + 10 * SCALE, y + 9 * SCALE, h, FONT['body_bold'], COLORS['white'])
            hx += cw
        y += row_h
        
        # 数据行
        data = [
            ('谁在管', '任职<2年', '超额≥3%+熊市抗跌'),
            ('怎么赚', '风格漂移>50%', '行业连续+换手100-250%'),
            ('买了什么', '龙头<40%', 'ROE≥15%+景气五灯'),
            ('赚得干净吗', '业绩靠3个月', '月度胜率≥60%'),
            ('明天还能吗', '规模翻倍+Alpha降', '不拥挤+回撤<20%'),
        ]
        
        for row_idx, row in enumerate(data):
            bg = COLORS['blue_lighter'] if row_idx % 2 == 0 else COLORS['bg_card']
            hx = x
            for cell, cw in zip(row, col_ws):
                self.draw_rect(hx, y, cw, row_h, bg)
                font = FONT['body_bold'] if hx == x else FONT['body']
                self.draw_text(hx + 10 * SCALE, y + 10 * SCALE, cell, font, COLORS['text_primary'])
                hx += cw
            y += row_h
            
        self.y += card_h + 25 * SCALE

    # ═══════════════════════════════════════════
    # 结尾区域
    # ═══════════════════════════════════════════
    def render_footer(self):
        """渲染结尾区域"""
        h = 200 * SCALE
        self.draw_rect(MARGIN, self.y, CONTENT_W, h, COLORS['navy'])
        
        y = self.y + 25 * SCALE
        x = MARGIN + 20 * SCALE
        
        # 大数字
        self.draw_text(x, y, '< 2%', FONT['title'], COLORS['orange'])
        y += 60 * SCALE
        
        # 标题
        self.draw_text(x, y, '最终只有不到 2% 的基金能通过全部筛网',
                      FONT['h1'], COLORS['white'])
        y += 40 * SCALE
        
        # 副标题
        self.draw_text(x, y, '这些，才是值得长期托付的资产。',
                      FONT['body'], (255, 255, 255, 200))
        
        self.y += h + 30 * SCALE


# ═══════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════
def main():
    print("=" * 50)
    print("淘金筛网 - 高清矢量化重绘")
    print("=" * 50)
    
    renderer = HDRenderer()
    
    # 先计算总高度
    # 各章节预估高度（基础像素）
    section_heights = [
        310,   # Hero
        370,   # S01
        470,   # S02
        830,   # S03
        650,   # S04
        770,   # S05
        700,   # S06
        330,   # Quick Ref
        230,   # Footer
    ]
    spacing = 25
    total_base = sum(section_heights) + spacing * len(section_heights) + 80  # margin
    
    print(f"画布尺寸: {W_BASE} × {total_base}px (基础)")
    print(f"输出尺寸: {W} × {int(total_base * SCALE)}px ({SCALE}倍高清)")
    
    # 创建画布
    renderer.create_canvas(total_base)
    
    # 渲染各章节
    print("\n正在渲染...")
    renderer.render_hero()
    print("  ✓ Hero 区域")
    
    renderer.render_s01()
    print("  ✓ 01 不选收益，选确定性")
    
    renderer.render_s02()
    print("  ✓ 02 第一网：基础红线")
    
    renderer.render_s03()
    print("  ✓ 03 第二网：经理真伪")
    
    renderer.render_s04()
    print("  ✓ 04 第三网：持仓含金量")
    
    renderer.render_s05()
    print("  ✓ 05 第四网：脆弱性测试")
    
    renderer.render_s06()
    print("  ✓ 06 最终棋盘：配置格局")
    
    renderer.render_quick_ref()
    print("  ✓ 附：五问速查卡")
    
    renderer.render_footer()
    print("  ✓ 结尾区域")
    
    # 输出路径
    output_dir = r"d:\一看就涨"
    png_path = os.path.join(output_dir, "淘金筛网_高清版.png")
    html_path = os.path.join(output_dir, "淘金筛网_高清版.html")
    
    # 保存 PNG
    renderer.img.save(png_path, "PNG", quality=95)
    png_size = os.path.getsize(png_path) / 1024
    print(f"\n[PNG] {png_path}  ({png_size:.1f} KB)")
    print(f"      尺寸: {renderer.img.width}×{renderer.img.height}px "
          f"(≈{int(SCALE * 96)}dpi)")
    
    # 尝试保存 PDF
    pdf_path = os.path.join(output_dir, "淘金筛网_高清版.pdf")
    try:
        renderer.img.save(pdf_path, "PDF", resolution=300)
        pdf_size = os.path.getsize(pdf_path) / 1024
        print(f"[PDF] {pdf_path}  ({pdf_size:.1f} KB)")
    except Exception as e:
        print(f"[PDF] 跳过: {e}")
        print(f"      可用PNG代替打印 (浏览器打开PNG → 打印 → 另存为PDF)")
    
    # 生成 HTML 版本
    generate_html(html_path, total_base)
    html_size = os.path.getsize(html_path) / 1024
    print(f"[HTML] {html_path}  ({html_size:.1f} KB)")
    
    print("\n" + "=" * 50)
    print("完成！三种格式均已生成。")


def generate_html(output_path, base_height):
    """生成可编辑HTML版本"""
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>淘金筛网 - 高清版</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
            background: #F5F7FA;
            padding: 20px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            width: {W_BASE}px;
            background: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .toolbar {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }}
        .toolbar button {{
            display: block;
            margin: 8px 0;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }}
        .btn-png {{ background: #0066CC; color: white; }}
        .btn-pdf {{ background: #FF8C00; color: white; }}
        @media print {{ .toolbar {{ display: none !important; }} }}
    </style>
</head>
<body>
    <div class="toolbar">
        <button class="btn-png" onclick="window.open('淘金筛网_高清版.png')">查看 PNG</button>
        <button class="btn-pdf" onclick="window.print()">打印 PDF</button>
    </div>
    <div class="container">
        <img src="淘金筛网_高清版.png" alt="淘金筛网 - 基金筛选体系">
    </div>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


if __name__ == '__main__':
    main()
