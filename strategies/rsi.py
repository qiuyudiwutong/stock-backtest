"""
RSI 策略
基于相对强弱指标的均值回归策略
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.base import BaseStrategy
from backtest.engine import Bar


class RSIStrategy(BaseStrategy):
    """RSI 策略"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70, **params):
        super().__init__(**params)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.prices = []
        self.in_position = False
    
    def on_init(self):
        print(f"📉 RSI 策略初始化：周期={self.period}, 超卖={self.oversold}, 超买={self.overbought}")
    
    def _calculate_rsi(self) -> float:
        """计算 RSI"""
        if len(self.prices) < self.period + 1:
            return 50.0
        
        prices_series = pd.Series(self.prices)
        delta = prices_series.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.period).mean().iloc[-1]
        avg_loss = loss.rolling(window=self.period).mean().iloc[-1]
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        
        # 数据不足时跳过
        if len(self.prices) < self.period + 10:
            return
        
        rsi = self._calculate_rsi()
        
        # RSI 低于超卖线，买入
        if rsi < self.oversold and not self.in_position:
            self.buy()
            self.in_position = True
            print(f"💰 RSI 超卖买入 @ {bar.close:.2f} (RSI={rsi:.1f})")
        
        # RSI 高于超买线，卖出
        elif rsi > self.overbought and self.in_position:
            self.sell()
            self.in_position = False
            print(f"💸 RSI 超买卖出 @ {bar.close:.2f} (RSI={rsi:.1f})")
