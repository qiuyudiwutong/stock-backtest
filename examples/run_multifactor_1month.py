"""
多因子选股策略回测 - 近 1 个月数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.engine import BacktestEngine
from strategies.multi_factor import MultiFactorStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_recent_data(days: int = 90):
    """
    生成近 90 天的模拟股票数据（3 个月）
    基于真实 A 股市场特征
    回测近 1 个月需要至少 60 天数据用于因子计算
    """
    print(f"📊 生成近{days}天交易数据...")
    
    # 生成交易日（约 22 个交易日/月）
    trading_days = days * 22 // 30
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=trading_days, freq='B')
    
    # 模拟 A 股价格走势（近期市场特征）
    np.random.seed(123)
    base_price = 25.0  # A 股平均股价
    
    # 近期 A 股特征：震荡走势，月波动±10%
    daily_drift = 0.0002  # 微小向上漂移
    daily_vol = 0.02  # 2% 日波动
    
    # 生成收益率序列（均值回归）
    returns = np.random.normal(daily_drift, daily_vol, trading_days)
    
    # 生成价格（限制在合理范围）
    prices = [base_price]
    for r in returns[1:]:
        new_price = prices[-1] * (1 + r)
        # 限制价格在合理范围（±50%）
        new_price = max(base_price * 0.5, min(base_price * 1.5, new_price))
        prices.append(new_price)
    prices = np.array(prices)
    
    # 生成 OHLCV 数据
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        daily_vol = abs(np.random.normal(0, 0.015))
        open_price = close * (1 + np.random.uniform(-daily_vol, daily_vol))
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.012)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.012)))
        volume = int(np.random.uniform(2000000, 8000000))
        
        data.append({
            'timestamp': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    
    # 保存为 CSV
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/recent_1month.csv', index=False)
    print(f"✅ 数据已生成：data/recent_1month.csv ({len(df)} 个交易日)")
    print(f"   时间范围：{df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
    print(f"   价格范围：{df['close'].min():.2f} - {df['close'].max():.2f}")
    
    return df


def run_multifactor_backtest():
    """运行多因子策略回测"""
    print("\n" + "="*60)
    print("🚀 多因子选股策略回测 - 近 1 个月")
    print("="*60 + "\n")
    
    # 生成数据（90 天数据，回测近 1 个月表现）
    df = generate_recent_data(days=90)
    
    # 初始化回测引擎
    engine = BacktestEngine(initial_cash=100000, commission_rate=0.0003)
    
    # 添加多因子策略
    engine.add_strategy(
        MultiFactorStrategy,
        lookback_period=20,
        top_k=10,
        rebalance_days=5
    )
    
    # 加载数据
    engine.load_dataframe(df)
    
    # 运行回测
    print("\n" + "-"*60)
    results = engine.run()
    
    # 生成报告
    print("\n" + "-"*60)
    report_path = engine.generate_report('reports/multifactor_1month_report.html')
    
    return results, df


def compare_strategies():
    """对比多因子与双均线策略"""
    print("\n" + "="*60)
    print("📊 策略对比：多因子 vs 双均线")
    print("="*60 + "\n")
    
    from strategies.sma_cross import SMACrossStrategy
    
    df = generate_recent_data(days=30)
    
    strategies = [
        ('多因子选股', MultiFactorStrategy, {'lookback_period': 20, 'rebalance_days': 5}),
        ('双均线', SMACrossStrategy, {'short_window': 10, 'long_window': 30}),
    ]
    
    results = {}
    for name, strategy_class, params in strategies:
        print(f"\n运行 {name} 策略...")
        engine = BacktestEngine(initial_cash=100000, commission_rate=0.0003)
        engine.add_strategy(strategy_class, **params)
        engine.load_dataframe(df.copy())
        results[name] = engine.run()
    
    # 对比结果
    print("\n" + "="*60)
    print("📈 策略对比结果")
    print("="*60)
    print(f"{'策略':<15} {'总收益':>10} {'年化':>10} {'夏普':>8} {'回撤':>10} {'胜率':>8}")
    print("-"*60)
    for name, result in results.items():
        print(f"{name:<15} {result.total_return:>9.2f}% {result.annual_return:>9.2f}% {result.sharpe_ratio:>8.2f} {result.max_drawdown:>9.2f}% {result.win_rate:>7.1f}%")
    print("="*60)
    
    return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'compare':
        compare_strategies()
    else:
        run_multifactor_backtest()
