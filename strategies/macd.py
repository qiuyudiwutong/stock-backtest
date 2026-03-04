"""
MACD 策略
基于 MACD 指标的趋势策略
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.base import BaseStrategy
from backtest.engine import Bar


class MACDStrategy(BaseStrategy):
    """MACD 策略"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **params):
        super().__init__(**params)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.prices = []
        self.in_position = False
    
    def on_init(self):
        print(f"📊 MACD 策略初始化：快={self.fast_period}, 慢={self.slow_period}, 信号={self.signal_period}")
    
    def _calculate_macd(self):
        """计算 MACD"""
        prices_series = pd.Series(self.prices)
        
        exp1 = prices_series.ewm(span=self.fast_period, adjust=False).mean()
        exp2 = prices_series.ewm(span=self.slow_period, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        
        # 数据不足时跳过
        if len(self.prices) < self.slow_period + self.signal_period:
            return
        
        macd, signal, hist = self._calculate_macd()
        
        # 当前值
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_hist = hist.iloc[-1]
        
        # 前一周期的值
        prev_macd = macd.iloc[-2]
        prev_signal = signal.iloc[-2]
        prev_hist = hist.iloc[-2]
        
        # MACD 上穿信号线（买入信号）
        if prev_macd <= prev_signal and current_macd > current_signal:
            if not self.in_position:
                self.buy()
                self.in_position = True
                print(f"💰 MACD 金叉买入 @ {bar.close:.2f}")
        
        # MACD 下穿信号线（卖出信号）
        elif prev_macd >= prev_signal and current_macd < current_signal:
            if self.in_position:
                self.sell()
                self.in_position = False
                print(f"💸 MACD 死叉卖出 @ {bar.close:.2f}")
