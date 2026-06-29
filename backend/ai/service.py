# -*- coding: utf-8 -*-
"""AI 服务 - DeepSeek 多模型路由"""
import json
import httpx
from typing import Optional, AsyncGenerator

from backend.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    OPENAI_API_KEY, AI_DEFAULT_MODEL,
)


class AIService:
    """AI 模型统一调用服务"""

    def __init__(self):
        self.default_model = AI_DEFAULT_MODEL

    def _get_client(self, model: str = None):
        model = model or self.default_model
        if model == "deepseek":
            return httpx.AsyncClient(
                base_url=DEEPSEEK_BASE_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        elif model == "openai":
            return httpx.AsyncClient(
                base_url="https://api.openai.com",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        else:
            raise ValueError(f"不支持的模型: {model}")

    async def chat(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """同步调用AI对话"""
        model = model or self.default_model
        model_name = DEEPSEEK_MODEL if model == "deepseek" else "gpt-4"

        async with self._get_client(model) as client:
            resp = await client.post(
                "/v1/chat/completions",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def stream_chat(
        self,
        messages: list[dict],
        model: str = None,
    ) -> AsyncGenerator[str, None]:
        """流式调用AI对话"""
        model = model or self.default_model
        model_name = DEEPSEEK_MODEL if model == "deepseek" else "gpt-4"

        async with self._get_client(model) as client:
            async with client.stream(
                "POST",
                "/v1/chat/completions",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    # ============ 专业分析 prompt ============

    TECH_ANALYSIS_PROMPT = """你是一位资深量化分析师。请基于以下股票技术数据，生成专业的技术分析报告：

股票：{name}({symbol})
最新价格：{price}
技术指标：
{indicators}

请按以下格式输出分析（使用中文）：
1. **趋势判断**：明确当前趋势（多头/空头/震荡）
2. **支撑位与压力位**：给出具体价格
3. **均线系统**：排列情况及含义
4. **MACD分析**：金叉/死叉/背离
5. **KDJ/RSI**：超买超卖状态
6. **量价关系**：成交量分析
7. **短线策略**：1-3日操作建议
8. **中线策略**：1-4周操作建议
9. **风险提示**：关键风险点
"""

    NEWS_ANALYSIS_PROMPT = """你是一位资深财经分析师。请分析以下新闻的金融市场影响：

新闻内容：{content}
新闻来源：{source}

请按JSON格式输出分析结果：
{{
  "summary": "新闻摘要（50字以内）",
  "sentiment": "positive/negative/neutral",
  "impact_level": "high/medium/low",
  "affected_sectors": ["行业1", "行业2"],
  "affected_stocks": ["股票1(代码)", "股票2(代码)"],
  "duration": "short/medium/long",
  "analysis": "详细分析（100字以内）"
}}"""

    MARKET_SENTIMENT_PROMPT = """你是一位资深市场分析师。请分析以下市场数据，判断当前市场情绪：

A股大盘表现：
{a_market}

全球市场表现：
{global_market}

资金面数据：
{fund_data}

请判断市场情绪等级（极度乐观/乐观/中性/谨慎/恐慌），并给出50字以内的理由。输出JSON格式：
{{"sentiment": "乐观", "score": 75, "reason": "..."}}"""

    DAILY_REVIEW_PROMPT = """你是一位首席投顾。请基于以下市场数据，生成今日大盘复盘报告：

指数表现：
{index_data}

板块表现：
{sector_data}

资金数据：
{fund_data}

请生成一份专业的收盘复盘，包含：
1. 市场综述
2. 热点板块
3. 资金变化
4. 赚钱效应
5. 风险提示
6. 明日展望

使用专业机构行文风格，500字左右。"""

    RESEARCH_PROMPT = """你是一位资深行业研究员。请针对以下投资标的进行深度研究分析：

标的：{name}({symbol})
类型：{report_type}

请生成一份专业研究报告，包含：
1. **公司概况**：核心业务与定位
2. **核心投资逻辑**：主要驱动因素
3. **竞争优势**：护城河分析
4. **财务分析**：关键指标
5. **估值分析**：合理估值区间
6. **风险分析**：主要风险点
7. **投资建议**：明确的操作建议

使用专业机构行文风格，800字左右，Markdown格式。"""


# 全局单例
ai_service = AIService()