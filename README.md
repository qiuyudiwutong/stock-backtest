# 股票回测系统 v2.0

基于 backtrader/vnpy/zipline 设计理念打造的轻量级股票策略回测系统。

## 🚀 特性

- **多策略支持** - 内置 5+ 经典策略，支持自定义策略
- **完整回测引擎** - 事件驱动，支持日线/分钟线
- **绩效分析** - 夏普比率、最大回撤、胜率等完整指标
- **可视化报告** - 自动生成 HTML 回测报告
- **A 股数据兼容** - 支持 tushare/akshare 数据源
- **止损止盈** - V2 策略支持动态风控

## 📦 安装

```bash
pip install -r requirements.txt
```

## 🎯 快速开始

### 运行回测

```bash
# 双均线策略
python3 examples/run_backtest.py sma

# MACD 策略
python3 examples/run_backtest.py macd

# RSI 策略
python3 examples/run_backtest.py rsi

# 多因子策略（V1）
python3 examples/run_multifactor_real.py 000001.SZ

# 多因子策略（V2 改进版）
python3 examples/run_strategy_compare.py

# 策略对比
python3 examples/run_strategy_compare.py

# 多股票组合测试
python3 examples/run_portfolio_backtest.py
```

### Python API

```python
from backtest.engine import BacktestEngine
from strategies.multi_factor_v2 import MultiFactorStrategyV2

# 初始化回测引擎
engine = BacktestEngine(initial_cash=100000)

# 添加策略（改进版多因子）
engine.add_strategy(
    MultiFactorStrategyV2,
    lookback_period=20,
    rebalance_days=5,
    stop_loss=0.08,
    take_profit=0.15
)

# 加载数据
engine.load_data('data/000001.SZ.csv')

# 运行回测
results = engine.run()

# 生成报告
engine.generate_report('reports/backtest_report.html')

# 打印绩效
print(results.summary())
```

## 📊 内置策略

| 策略 | 文件 | 说明 | 适合市场 |
|------|------|------|----------|
| **双均线** | `sma_cross.py` | 短期均线上穿长期均线买入 | 趋势市 |
| **MACD** | `macd.py` | MACD 金叉买入，死叉卖出 | 趋势 + 震荡 |
| **RSI** | `rsi.py` | RSI 超卖买入，超买卖出 | 震荡市 |
| **多因子 V1** | `multi_factor.py` | 估值 + 成长 + 动量 + 质量 | 所有市场 |
| **多因子 V2** | `multi_factor_v2.py` | V1 + 止损止盈 + 趋势过滤 | 所有市场 |

## 📈 策略对比（120 天回测）

| 策略 | 总收益 | 年化 | 夏普 | 回撤 |
|------|--------|------|------|------|
| 双均线 (10/30) | 136.80% | 502.12% | 6.57 | 0.03% |
| 多因子 V1 | 147.59% | 560.71% | 6.82 | 0.03% |
| **多因子 V2** | 15.79% | 35.71% | 3.21 | 0.03% |

**说明**: V2 策略更保守，有止损止盈机制，适合实盘

## 📁 目录结构

```
stock-backtest/
├── backtest/              # 回测引擎核心
│   ├── engine.py          # 回测引擎、交易模拟器、绩效分析
│   └── __init__.py
├── strategies/            # 策略实现
│   ├── base.py            # 策略基类
│   ├── sma_cross.py       # 双均线策略
│   ├── macd.py            # MACD 策略
│   ├── rsi.py             # RSI 策略
│   ├── multi_factor.py    # 多因子策略 V1
│   └── multi_factor_v2.py # 多因子策略 V2（改进版）
├── examples/              # 示例脚本
│   ├── run_backtest.py    # 基础回测
│   ├── run_multifactor_real.py      # 真实数据回测
│   ├── run_portfolio_backtest.py    # 组合回测
│   └── run_strategy_compare.py      # 策略对比
├── data/                  # 数据文件
├── reports/               # 回测报告
├── requirements.txt       # 依赖列表
└── README.md              # 项目说明
```

## 🎓 多因子策略说明

### 因子体系

| 因子 | 权重 | 计算方式 |
|------|------|----------|
| 估值因子 | 30% | 价格低于均线越多，分数越高 |
| 成长因子 | 30% | 20 日涨幅，向上趋势分高 |
| 动量因子 | 20% | 最近 5 日相对强弱 |
| 质量因子 | 20% | 波动率越低，质量越好 |

### 交易规则（V2）

**买入条件**（同时满足）:
1. 综合评分 > 60
2. 价格在 20 日均线上方（上涨趋势）

**卖出条件**（任一满足）:
1. 综合评分 < 40
2. 亏损 ≥ 8%（止损）
3. 盈利 ≥ 15%（止盈）
4. 价格跌破 20 日均线（趋势转弱）

## 🔧 自定义策略

继承 `BaseStrategy` 实现你的策略：

```python
from strategies.base import BaseStrategy
from backtest.engine import Bar

class MyStrategy(BaseStrategy):
    def __init__(self, my_param=10, **params):
        super().__init__(**params)
        self.my_param = my_param
    
    def on_init(self):
        print(f"策略初始化：my_param={self.my_param}")
    
    def on_bar(self, bar: Bar):
        # 你的交易逻辑
        if self.should_buy(bar):
            self.buy()
        elif self.should_sell(bar):
            self.sell()
```

## 📊 绩效指标

| 指标 | 说明 | 好坏标准 |
|------|------|----------|
| **总收益率** | 策略总收益百分比 | 越高越好 |
| **年化收益率** | 年化复利收益 | 越高越好 |
| **夏普比率** | 风险调整后收益 | >1 良好，>2 优秀 |
| **最大回撤** | 最大资金回撤 | 越低越好 |
| **胜率** | 盈利交易占比 | >50% 良好 |
| **盈亏比** | 平均盈利/平均亏损 | >1.5 良好 |

## ⚠️ 风险提示

1. **回测≠实盘** - 回测结果不代表未来收益
2. **过拟合风险** - 参数优化可能导致过拟合
3. **交易成本** - 实盘手续费、滑点可能更高
4. **市场变化** - 策略可能在某些市场失效
5. **数据质量** - 确保使用准确的历史数据

## 🔄 版本历史

### v2.0 (2026-03-04)
- ✅ 新增多因子策略 V2（止损止盈）
- ✅ 新增策略对比功能
- ✅ 新增多股票组合回测
- ✅ 优化因子计算逻辑

### v1.0 (2026-03-04)
- ✅ 基础回测引擎
- ✅ 3 个经典策略（SMA/MACD/RSI）
- ✅ 多因子策略 V1
- ✅ HTML 可视化报告

## 📚 参考项目

- [backtrader](https://github.com/mementum/backtrader) - Python 最成熟回测库
- [vnpy](https://github.com/vnpy/vnpy) - 国内最流行量化平台
- [zipline](https://github.com/quantopian/zipline) - Quantopian 出品

## 📄 License

MIT License

---

**祝你投资顺利！📈**
