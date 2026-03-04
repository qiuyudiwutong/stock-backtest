"""
策略对比回测：V1 vs V2
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.engine import BacktestEngine
from strategies.multi_factor import MultiFactorStrategy
from strategies.multi_factor_v2 import MultiFactorStrategyV2
from strategies.sma_cross import SMACrossStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_stock_data(ts_code: str = '000001.SZ', days: int = 120, seed: int = 456):
    """生成股票数据"""
    np.random.seed(seed)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
    trading_days = len(dates)
    
    base_price = 12.5
    daily_vol = 0.02
    
    # 生成带趋势的价格
    trend = np.linspace(-0.05, 0.2, trading_days)  # -5% 到 +20%
    noise = np.random.normal(0, daily_vol, trading_days)
    returns = trend + noise
    
    prices = [base_price]
    for r in returns[1:]:
        r = max(-0.08, min(0.08, r))
        new_price = prices[-1] * (1 + r)
        new_price = max(base_price * 0.6, min(base_price * 1.8, new_price))
        prices.append(new_price)
    prices = np.array(prices)
    
    # 生成 OHLCV
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        daily_range = abs(np.random.normal(0, 0.01))
        open_price = close * (1 + np.random.uniform(-daily_range, daily_range))
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.008)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.008)))
        volume = int(np.random.uniform(3000000, 15000000))
        
        data.append({
            'timestamp': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    return pd.DataFrame(data)


def compare_all_strategies():
    """对比所有策略"""
    print("\n" + "="*70)
    print("📊 策略对比回测 - A 股多因子策略演进")
    print("="*70 + "\n")
    
    df = generate_stock_data('000001.SZ', days=120, seed=456)
    
    strategies = [
        ('双均线 (10/30)', SMACrossStrategy, {'short_window': 10, 'long_window': 30}),
        ('多因子 V1', MultiFactorStrategy, {'lookback_period': 20, 'rebalance_days': 5}),
        ('多因子 V2', MultiFactorStrategyV2, {'lookback_period': 20, 'rebalance_days': 5, 'stop_loss': 0.08, 'take_profit': 0.15}),
    ]
    
    results = {}
    
    for name, strategy_class, params in strategies:
        print(f"\n▶ 运行 {name}...")
        engine = BacktestEngine(initial_cash=100000, commission_rate=0.0003)
        engine.add_strategy(strategy_class, **params)
        engine.load_dataframe(df.copy())
        result = engine.run()
        results[name] = result
    
    # 对比结果
    print("\n" + "="*70)
    print("📈 策略对比结果汇总")
    print("="*70)
    print(f"{'策略':<18} {'总收益':>10} {'年化':>10} {'夏普':>8} {'回撤':>10} {'交易':>6}")
    print("-"*70)
    
    for name, result in results.items():
        print(f"{name:<18} {result.total_return:>9.2f}% {result.annual_return:>9.2f}% {result.sharpe_ratio:>8.2f} {result.max_drawdown:>9.2f}% {result.total_trades:>6}")
    
    print("="*70)
    
    # 找出最佳
    best = max(results.items(), key=lambda x: x[1].total_return)
    best_sharpe = max(results.items(), key=lambda x: x[1].sharpe_ratio)
    best_calmar = max(results.items(), key=lambda x: x[1].annual_return / x[1].max_drawdown if x[1].max_drawdown > 0 else 0)
    
    print(f"\n🏆 最佳收益：{best[0]} ({best[1].total_return:.2f}%)")
    print(f"🎯 最佳夏普：{best_sharpe[0]} ({best_sharpe[1].sharpe_ratio:.2f})")
    print(f"⚖️  最佳卡玛：{best_calmar[0]} ({best_calmar[1].annual_return / best_calmar[1].max_drawdown:.2f})")
    print("="*70)
    
    return results


def backtest_with_different_stocks():
    """在不同股票上测试 V2 策略"""
    print("\n" + "="*70)
    print("📊 多因子 V2 策略 - 多股票测试")
    print("="*70 + "\n")
    
    stocks = [
        ('000001.SZ', '平安银行', 12.5, 789),
        ('600519.SS', '贵州茅台', 1600, 790),
        ('000858.SZ', '五粮液', 50, 791),
        ('601318.SS', '中国平安', 50, 792),
        ('300750.SZ', '宁德时代', 250, 793),
    ]
    
    results = {}
    
    for ts_code, name, base_price, seed in stocks:
        df = generate_stock_data(ts_code, days=120, seed=seed)
        
        engine = BacktestEngine(initial_cash=100000, commission_rate=0.0003)
        engine.add_strategy(MultiFactorStrategyV2, lookback_period=20, rebalance_days=5)
        engine.load_dataframe(df)
        result = engine.run()
        
        results[name] = result
    
    # 汇总
    print("\n" + "="*70)
    print("📈 多股票测试结果")
    print("="*70)
    print(f"{'股票':<12} {'总收益':>10} {'夏普':>8} {'回撤':>10} {'交易':>6}")
    print("-"*70)
    
    for name, result in results.items():
        print(f"{name:<12} {result.total_return:>9.2f}% {result.sharpe_ratio:>8.2f} {result.max_drawdown:>9.2f}% {result.total_trades:>6}")
    
    print("="*70)
    
    return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'stocks':
        backtest_with_different_stocks()
    else:
        compare_all_strategies()
