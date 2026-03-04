# Stock Backtest System

基于 backtrader/vnpy/zipline 设计理念打造的轻量级股票策略回测系统。

## 🚀 特性

- **多策略支持** - 内置经典策略，支持自定义策略
- **完整回测引擎** - 事件驱动，支持日线/分钟线
- **绩效分析** - 夏普比率、最大回撤、胜率等完整指标
- **可视化报告** - 自动生成 HTML 回测报告
- **A 股数据兼容** - 支持 tushare/akshare 数据源

## 📦 安装

```bash
pip install -r requirements.txt
```

## 🎯 快速开始

```python
from backtest.engine import BacktestEngine
from strategies.sma_cross import SMACrossStrategy

# 初始化回测引擎
engine = BacktestEngine(initial_cash=100000)

# 添加策略
engine.add_strategy(SMACrossStrategy, short_window=10, long_window=30)

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

| 策略 | 说明 |
|------|------|
| SMA Cross | 双均线交叉策略 |
| MACD | MACD 指标策略 |
| RSI | 相对强弱指标策略 |
| Bollinger | 布林带策略 |

## 📁 目录结构

```
stock-backtest/
├── backtest/          # 回测引擎核心
│   ├── engine.py      # 回测引擎
│   ├── broker.py      # 模拟器
│   └── analyzer.py    # 绩效分析
├── strategies/        # 策略实现
│   ├── base.py        # 策略基类
│   ├── sma_cross.py   # 双均线策略
│   └── ...
├── data/              # 数据文件
├── utils/             # 工具函数
├── reports/           # 回测报告
└── README.md
```

## 📈 绩效指标

- **总收益率** - 策略总收益百分比
- **年化收益率** - 年化复利收益
- **夏普比率** - 风险调整后收益
- **最大回撤** - 最大资金回撤
- **胜率** - 盈利交易占比
- **盈亏比** - 平均盈利/平均亏损

## 🔧 配置

在 `config.py` 中配置：

```python
# 初始资金
INITIAL_CASH = 100000

# 手续费率
COMMISSION_RATE = 0.0003

# 滑点
SLIPPAGE = 0.001

# 数据源
DATA_SOURCE = 'akshare'  # akshare / tushare / csv
```

## 📝 自定义策略

继承 `BaseStrategy` 实现你的策略：

```python
from backtest.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, **params):
        super().__init__(**params)
    
    def on_bar(self, bar):
        # 你的交易逻辑
        if self.should_buy(bar):
            self.buy()
        elif self.should_sell(bar):
            self.sell()
```

## ⚠️ 风险提示

回测结果不代表未来收益，实盘需谨慎！

---

**版本**: 1.0.0  
**License**: MIT
