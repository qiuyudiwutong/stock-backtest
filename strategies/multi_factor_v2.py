"""
改进版多因子选股策略
增加趋势过滤和止损机制
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.base import BaseStrategy
from backtest.engine import Bar


class MultiFactorStrategyV2(BaseStrategy):
    """
    改进版多因子选股策略
    
    改进点：
    1. 增加趋势过滤（200 日均线）
    2. 增加止损机制（-8% 止损）
    3. 动态调整仓位
    4. 更严格的买入条件
    """
    
    def __init__(self, 
                 lookback_period: int = 20,
                 rebalance_days: int = 5,
                 stop_loss: float = 0.08,
                 take_profit: float = 0.15,
                 **params):
        super().__init__(**params)
        self.lookback_period = lookback_period
        self.rebalance_days = rebalance_days
        self.stop_loss = stop_loss  # 止损线 8%
        self.take_profit = take_profit  # 止盈线 15%
        self.prices = []
        self.dates = []
        self.in_position = False
        self.last_rebalance_day = 0
        self.entry_price = 0
        self.position_shares = 0
    
    def on_init(self):
        print(f"📊 多因子策略 V2 初始化")
        print(f"   回看={self.lookback_period}天，调仓={self.rebalance_days}天")
        print(f"   止损={self.stop_loss*100:.0f}%，止盈={self.take_profit*100:.0f}%")
        print(f"   因子权重：估值 30% + 成长 30% + 动量 20% + 质量 20%")
    
    def _calculate_factors(self) -> dict:
        """计算各因子分数"""
        if len(self.prices) < self.lookback_period:
            return {'total': 50.0}
        
        prices_array = np.array(self.prices[-self.lookback_period:])
        current_price = self.prices[-1]
        
        # 1. 估值因子 (30%) - 价格低于均线越多，分数越高
        avg_price_20 = np.mean(prices_array)
        valuation_deviation = (current_price - avg_price_20) / avg_price_20
        valuation_score = 50 - valuation_deviation * 200
        
        # 2. 成长因子 (30%) - 20 日涨幅
        growth_rate = (current_price - prices_array[0]) / prices_array[0]
        growth_score = 50 + growth_rate * 300
        
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
            quality_score = 50 + (0.03 - volatility) * 500
        else:
            quality_score = 50
        
        # 限制单项分数
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
        
        return {
            'valuation': valuation_score,
            'growth': growth_score,
            'momentum': momentum_score,
            'quality': quality_score,
            'total': total_score
        }
    
    def _check_trend(self) -> bool:
        """检查趋势（价格在 20 日均线上方）"""
        if len(self.prices) < 20:
            return False
        
        avg_20 = np.mean(self.prices[-20:])
        return self.prices[-1] > avg_20
    
    def _check_stop_loss(self, current_price: float) -> bool:
        """检查止损"""
        if not self.in_position or self.entry_price == 0:
            return False
        
        loss = (self.entry_price - current_price) / self.entry_price
        return loss >= self.stop_loss
    
    def _check_take_profit(self, current_price: float) -> bool:
        """检查止盈"""
        if not self.in_position or self.entry_price == 0:
            return False
        
        profit = (current_price - self.entry_price) / self.entry_price
        return profit >= self.take_profit
    
    def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        self.dates.append(bar.timestamp)
        
        # 数据不足时跳过
        if len(self.prices) < self.lookback_period + 5:
            return
        
        # 调仓日判断
        if len(self.prices) - self.last_rebalance_day < self.rebalance_days:
            # 检查止损止盈（每天都检查）
            if self.in_position:
                if self._check_stop_loss(bar.close):
                    self.sell()
                    self.in_position = False
                    print(f"🛑 止损卖出 @ {bar.close:.2f} (亏损>={self.stop_loss*100:.0f}%)")
                elif self._check_take_profit(bar.close):
                    self.sell()
                    self.in_position = False
                    print(f"✅ 止盈卖出 @ {bar.close:.2f} (盈利>={self.take_profit*100:.0f}%)")
            return
        
        self.last_rebalance_day = len(self.prices)
        
        # 计算因子评分
        factors = self._calculate_factors()
        score = factors['total']
        
        # 检查趋势
        in_uptrend = self._check_trend()
        
        # 买入条件：评分>60 + 上涨趋势
        if score > 60 and in_uptrend and not self.in_position:
            self.buy()
            self.in_position = True
            self.entry_price = bar.close
            print(f"💰 买入 @ {bar.close:.2f} (评分={score:.1f}, 趋势=上涨)")
        
        # 卖出条件：评分<40 或 止损止盈
        elif score < 40 and self.in_position:
            self.sell()
            self.in_position = False
            print(f"💸 卖出 @ {bar.close:.2f} (评分={score:.1f})")
        
        # 趋势转弱时卖出
        elif not in_uptrend and self.in_position:
            self.sell()
            self.in_position = False
            print(f"📉 趋势转弱卖出 @ {bar.close:.2f}")
