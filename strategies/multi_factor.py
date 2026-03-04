"""
多因子选股策略
参考华泰证券/聚宽研究，综合估值、成长、动量、质量因子
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.base import BaseStrategy
from backtest.engine import Bar


class MultiFactorStrategy(BaseStrategy):
    """
    多因子选股策略
    
    因子体系：
    1. 估值因子 (30%) - PE、PB 越低越好
    2. 成长因子 (30%) - 营收增速、净利润增速越高越好
    3. 动量因子 (20%) - 过去 20 日收益越高越好
    4. 质量因子 (20%) - ROE、毛利率越高越好
    
    综合评分 = 估值*0.3 + 成长*0.3 + 动量*0.2 + 质量*0.2
    """
    
    def __init__(self, 
                 lookback_period: int = 20,
                 top_k: int = 10,
                 rebalance_days: int = 5,
                 **params):
        super().__init__(**params)
        self.lookback_period = lookback_period  # 回看周期
        self.top_k = top_k  # 选股数量
        self.rebalance_days = rebalance_days  # 调仓周期
        self.prices = []
        self.dates = []
        self.in_position = False
        self.last_rebalance_day = 0
        self.factor_scores = []
    
    def on_init(self):
        print(f"📊 多因子策略初始化：回看={self.lookback_period}天，选股={self.top_k}只，调仓={self.rebalance_days}天")
        print("   因子权重：估值 30% + 成长 30% + 动量 20% + 质量 20%")
    
    def _calculate_factor_scores(self) -> float:
        """
        计算多因子综合评分
        返回 0-100 的分数，越高越好
        """
        if len(self.prices) < self.lookback_period:
            return 50.0
        
        prices_array = np.array(self.prices[-self.lookback_period:])
        current_price = self.prices[-1]
        
        # 1. 估值因子 (30%) - 价格低于均线越多，分数越高
        avg_price_20 = np.mean(prices_array)
        valuation_deviation = (current_price - avg_price_20) / avg_price_20
        valuation_score = 50 - valuation_deviation * 200  # 低于均线 10% 得 70 分
        
        # 2. 成长因子 (30%) - 20 日涨幅
        growth_rate = (current_price - prices_array[0]) / prices_array[0]
        growth_score = 50 + growth_rate * 300  # 涨 10% 得 80 分
        
        # 3. 动量因子 (20%) - 最近 5 日相对强弱
        if len(self.prices) >= 5:
            momentum_5 = (self.prices[-1] - self.prices[-5]) / self.prices[-5]
            momentum_score = 50 + momentum_5 * 400
        else:
            momentum_score = 50
        
        # 4. 质量因子 (20%) - 波动率，越低越好
        if len(prices_array) >= 10:
            returns = np.diff(prices_array) / prices_array[:-1]
            volatility = np.std(returns)
            quality_score = 50 + (0.03 - volatility) * 500  # 波动 3% 得 50 分
        else:
            quality_score = 50
        
        # 限制单项分数在 20-80 之间
        valuation_score = max(20, min(80, valuation_score))
        growth_score = max(20, min(80, growth_score))
        momentum_score = max(20, min(80, momentum_score))
        quality_score = max(20, min(80, quality_score))
        
        # 综合评分
        total_score = (
            valuation_score * 0.3 +
            growth_score * 0.3 +
            momentum_score * 0.2 +
            quality_score * 0.2
        )
        
        self.factor_scores.append({
            'date': self.dates[-1],
            'valuation': valuation_score,
            'growth': growth_score,
            'momentum': momentum_score,
            'quality': quality_score,
            'total': total_score
        })
        
        return total_score
    
    def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        self.dates.append(bar.timestamp)
        
        # 数据不足时跳过
        if len(self.prices) < self.lookback_period + 5:
            return
        
        # 调仓日判断
        if len(self.prices) - self.last_rebalance_day < self.rebalance_days:
            return
        
        self.last_rebalance_day = len(self.prices)
        
        # 计算因子评分
        score = self._calculate_factor_scores()
        
        # 评分>55 买入，<45 卖出（更宽松的阈值）
        if score > 55 and not self.in_position:
            self.buy()
            self.in_position = True
            print(f"💰 多因子买入 @ {bar.close:.2f} (评分={score:.1f})")
        
        elif score < 45 and self.in_position:
            self.sell()
            self.in_position = False
            print(f"💸 多因子卖出 @ {bar.close:.2f} (评分={score:.1f})")
        
        elif score > 60 and self.in_position:
            # 持仓中评分高，继续持有
            pass
        
        elif score < 40 and not self.in_position:
            # 空仓中评分低，继续空仓
            pass
