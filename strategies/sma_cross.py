"""
双均线交叉策略
经典趋势跟踪策略
"""

import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.base import BaseStrategy
from backtest.engine import Bar


class SMACrossStrategy(BaseStrategy):
    """双均线交叉策略"""
    
    def __init__(self, short_window: int = 10, long_window: int = 30, **params):
        super().__init__(**params)
        self.short_window = short_window
        self.long_window = long_window
        self.prices = []
        self.in_position = False
    
    def on_init(self):
        print(f"📈 双均线策略初始化：短期={self.short_window}, 长期={self.long_window}")
    
    def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        
        # 数据不足时跳过
        if len(self.prices) < self.long_window:
            return
        
        # 计算均线
        prices_series = pd.Series(self.prices)
        short_sma = prices_series.tail(self.short_window).mean()
        long_sma = prices_series.tail(self.long_window).mean()
        
        # 前一周期的均线
        prev_short = prices_series.tail(self.short_window + 1).head(self.short_window).mean()
        prev_long = prices_series.tail(self.long_window + 1).head(self.long_window).mean()
        
        # 金叉：短期上穿长期
        if prev_short <= prev_long and short_sma > long_sma:
            if not self.in_position:
                self.buy()
                self.in_position = True
                print(f"💰 金叉买入 @ {bar.close:.2f}")
        
        # 死叉：短期下穿长期
        elif prev_short >= prev_long and short_sma < long_sma:
            if self.in_position:
                self.sell()
                self.in_position = False
                print(f"💸 死叉卖出 @ {bar.close:.2f}")
