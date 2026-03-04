"""
示例回测脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.engine import BacktestEngine
from strategies.sma_cross import SMACrossStrategy
from strategies.macd import MACDStrategy
from strategies.rsi import RSIStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_sample_data():
    """生成示例股票数据"""
    print("📊 生成示例数据...")
    
    # 生成 2 年的交易日数据（约 500 个交易日）
    dates = pd.date_range(start='2022-01-01', periods=500, freq='B')  # 工作日
    
    # 模拟股票价格走势（随机游走 + 趋势）
    np.random.seed(42)
    base_price = 10.0
    returns = np.random.normal(0.0005, 0.02, 500)  # 日均收益 0.05%，波动 2%
    prices = base_price * np.cumprod(1 + returns)
    
    # 生成 OHLCV 数据
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        daily_volatility = abs(np.random.normal(0, 0.015))
        open_price = close * (1 + np.random.uniform(-daily_volatility, daily_volatility))
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
        volume = int(np.random.uniform(1000000, 5000000))
        
        data.append({
            'timestamp': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    
    # 保存为 CSV
    df.to_csv('data/sample_stock.csv', index=False)
    print(f"✅ 示例数据已生成：data/sample_stock.csv ({len(df)} 条)")
    
    return df


def run_backtest(strategy_type: str = 'sma'):
    """运行回测"""
    print("\n" + "="*50)
    print("🚀 股票策略回测系统 v1.0")
    print("="*50 + "\n")
    
    # 生成示例数据
    df = generate_sample_data()
    
    # 初始化回测引擎
    engine = BacktestEngine(initial_cash=100000, commission_rate=0.0003)
    
    # 添加策略
    if strategy_type == 'sma':
        engine.add_strategy(SMACrossStrategy, short_window=10, long_window=30)
    elif strategy_type == 'macd':
        engine.add_strategy(MACDStrategy, fast_period=12, slow_period=26, signal_period=9)
    elif strategy_type == 'rsi':
        engine.add_strategy(RSIStrategy, period=14, oversold=30, overbought=70)
    else:
        raise ValueError(f"未知策略类型：{strategy_type}")
    
    # 加载数据
    engine.load_dataframe(df)
    
    # 运行回测
    print("\n" + "-"*50)
    results = engine.run()
    
    # 生成报告
    print("\n" + "-"*50)
    engine.generate_report('reports/backtest_report.html')
    
    return results


if __name__ == '__main__':
    import sys
    strategy = sys.argv[1] if len(sys.argv) > 1 else 'sma'
    run_backtest(strategy)
