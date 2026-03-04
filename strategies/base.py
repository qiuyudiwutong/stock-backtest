"""
策略基类
所有自定义策略需继承此类
"""

from abc import ABC, abstractmethod
from typing import Optional
from backtest.engine import Bar, BacktestEngine


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, **params):
        self.params = params
        self.engine: Optional[BacktestEngine] = None
        self.position = 0  # 当前持仓数量
        self.cash = 0  # 可用现金
    
    def on_init(self):
        """策略初始化"""
        pass
    
    @abstractmethod
    def on_bar(self, bar: Bar):
        """每根 K 线触发"""
        pass
    
    def buy(self, shares: int = None, price: float = None):
        """买入"""
        if self.engine is None:
            return
        
        bar = self.engine._get_bar(self.engine.current_bar)
        price = price or bar.close
        
        if shares is None:
            # 默认全仓买入
            available_cash = self.engine.broker.cash * 0.95
            shares = int(available_cash / price)
        
        self.engine.broker.buy(price, shares, bar.timestamp)
        self.position = self.engine.broker.position.shares
    
    def sell(self, shares: int = None, price: float = None):
        """卖出"""
        if self.engine is None:
            return
        
        bar = self.engine._get_bar(self.engine.current_bar)
        price = price or bar.close
        
        if shares is None:
            # 默认全仓卖出
            shares = self.engine.broker.position.shares
        
        self.engine.broker.sell(price, shares, bar.timestamp)
        self.position = self.engine.broker.position.shares
    
    def get_position(self) -> int:
        """获取当前持仓"""
        return self.engine.broker.position.shares if self.engine else 0
    
    def get_cash(self) -> float:
        """获取当前现金"""
        return self.engine.broker.cash if self.engine else 0
    
    def get_equity(self) -> float:
        """获取当前总资产"""
        if self.engine is None:
            return 0
        bar = self.engine._get_bar(self.engine.current_bar)
        return self.engine.broker.get_equity(bar.close)
