"""
A 股多股票组合回测
测试多只股票，验证策略普适性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.engine import BacktestEngine
from strategies.multi_factor import MultiFactorStrategy
from strategies.sma_cross import SMACrossStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_stock_data(ts_code: str, days: int = 90, seed: int = None):
    """生成单只股票数据"""
    if seed:
        np.random.seed(seed)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
    trading_days = len(dates)
    
    # 不同股票设定不同价格区间
    price_ranges = {
        '000001.SZ': (10, 15),    # 平安银行
        '600519.SS': (1400, 1800), # 贵州茅台
        '000858.SZ': (40, 60),     # 五粮液
        '601318.SS': (40, 60),     # 中国平安
        '300750.SZ': (200, 300),   # 宁德时代
    }
    
    price_range = price_ranges.get(ts_code, (20, 40))
    base_price = (price_range[0] + price_range[1]) / 2
    
    # 生成价格（随机游走）
    daily_vol = 0.02
    returns = np.random.normal(0.0002, daily_vol, trading_days)
    
    prices = [base_price]
    for r in returns[1:]:
        new_price = prices[-1] * (1 + r)
        new_price = max(price_range[0] * 0.8, min(price_range[1] * 1.2, new_price))
        prices.append(new_price)
    prices = np.array(prices)
    
    # 生成 OHLCV
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        daily_range = abs(np.random.normal(0, 0.01))
        open_price = close * (1 + np.random.uniform(-daily_range, daily_range))
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.008)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.008)))
        volume = int(np.random.uniform(2000000, 20000000))
        
        data.append({
            'timestamp': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    return pd.DataFrame(data)


def backtest_portfolio():
    """回测多股票组合"""
    print("\n" + "="*60)
    print("📊 A 股多股票组合回测 - 多因子策略")
    print("="*60 + "\n")
    
    # 股票池
    stocks = [
        ('000001.SZ', '平安银行'),
        ('600519.SS', '贵州茅台'),
        ('000858.SZ', '五粮液'),
        ('601318.SS', '中国平安'),
        ('300750.SZ', '宁德时代'),
    ]
    
    results = {}
    
    for ts_code, name in stocks:
        print(f"\n▶ 回测 {name} ({ts_code})...")
        
        # 生成数据
        df = generate_stock_data(ts_code, days=90, seed=hash(ts_code) % 1000)
        
        # 回测
        engine = BacktestEngine(initial_cash=100000, commission_rate=0.0003)
        engine.add_strategy(MultiFactorStrategy, lookback_period=20, rebalance_days=5)
        engine.load_dataframe(df)
        result = engine.run()
        
        results[ts_code] = {
            'name': name,
            'result': result,
            'price_change': (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        }
    
    # 汇总结果
    print("\n" + "="*60)
    print("📈 组合回测汇总")
    print("="*60)
    print(f"{'股票':<12} {'名称':<10} {'策略收益':>10} {'买入持有':>10} {'超额':>8} {'回撤':>8}")
    print("-"*60)
    
    total_excess = 0
    for ts_code, data in results.items():
        strategy_return = data['result'].total_return
        buy_hold = data['price_change']
        excess = strategy_return - buy_hold
        total_excess += excess
        print(f"{ts_code:<12} {data['name']:<10} {strategy_return:>9.2f}% {buy_hold:>9.2f}% {excess:>7.2f}% {data['result'].max_drawdown:>7.2f}%")
    
    print("-"*60)
    avg_excess = total_excess / len(results)
    print(f"{'平均超额收益':<22} {'':>10} {'':>10} {avg_excess:>7.2f}%")
    print("="*60)
    
    return results


if __name__ == '__main__':
    backtest_portfolio()
