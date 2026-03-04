"""
股票回测系统 - 核心引擎
参考 backtrader/vnpy 设计
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Bar:
    """K 线数据"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Trade:
    """交易记录"""
    timestamp: datetime
    direction: str  # 'BUY' or 'SELL'
    price: float
    shares: int
    commission: float


@dataclass
class Position:
    """持仓"""
    symbol: str
    shares: int = 0
    avg_cost: float = 0.0


@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    equity_curve: List[float] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    
    def summary(self) -> str:
        """打印绩效摘要"""
        return f"""
═══════════════════════════════════════
           回测绩效报告
═══════════════════════════════════════
总收益率：     {self.total_return:>10.2f}%
年化收益率：   {self.annual_return:>10.2f}%
夏普比率：     {self.sharpe_ratio:>10.2f}
最大回撤：     {self.max_drawdown:>10.2f}%
胜率：         {self.win_rate:>10.2f}%
盈亏比：       {self.profit_loss_ratio:>10.2f}
总交易次数：   {self.total_trades:>10d}
盈利交易：     {self.winning_trades:>10d}
═══════════════════════════════════════
"""


class Broker:
    """交易模拟器"""
    
    def __init__(self, initial_cash: float, commission_rate: float = 0.0003):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.position = Position(symbol='STOCK')
        self.trades: List[Trade] = []
    
    def buy(self, price: float, shares: int, timestamp: datetime) -> Optional[Trade]:
        """买入"""
        cost = price * shares
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        if total_cost > self.cash:
            shares = int((self.cash * 0.95) / price)  # 留 5% 现金
            if shares == 0:
                return None
            cost = price * shares
            commission = cost * self.commission_rate
            total_cost = cost + commission
        
        self.cash -= total_cost
        
        # 更新持仓成本
        old_value = self.position.shares * self.position.avg_cost
        new_value = cost
        total_shares = self.position.shares + shares
        self.position.avg_cost = (old_value + new_value) / total_shares if total_shares > 0 else 0
        self.position.shares = total_shares
        
        trade = Trade(timestamp, 'BUY', price, shares, commission)
        self.trades.append(trade)
        return trade
    
    def sell(self, price: float, shares: int, timestamp: datetime) -> Optional[Trade]:
        """卖出"""
        shares = min(shares, self.position.shares)
        if shares == 0:
            return None
        
        revenue = price * shares
        commission = revenue * self.commission_rate
        net_revenue = revenue - commission
        
        self.cash += net_revenue
        self.position.shares -= shares
        
        trade = Trade(timestamp, 'SELL', price, shares, commission)
        self.trades.append(trade)
        return trade
    
    def get_equity(self, current_price: float) -> float:
        """获取当前总资产"""
        return self.cash + self.position.shares * current_price


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_cash: float = 100000, commission_rate: float = 0.0003):
        self.initial_cash = initial_cash
        self.broker = Broker(initial_cash, commission_rate)
        self.strategy = None
        self.data: pd.DataFrame = None
        self.equity_curve: List[float] = []
        self.current_bar = 0
    
    def add_strategy(self, strategy_class, **params):
        """添加策略"""
        self.strategy = strategy_class(**params)
        self.strategy.engine = self
        return self
    
    def load_data(self, filepath: str):
        """加载 CSV 数据"""
        self.data = pd.read_csv(filepath)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.data = self.data.sort_values('timestamp').reset_index(drop=True)
        print(f"✅ 数据加载完成：{len(self.data)} 条 K 线")
        return self
    
    def load_dataframe(self, df: pd.DataFrame):
        """直接加载 DataFrame"""
        self.data = df.copy()
        if 'timestamp' in self.data.columns:
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.data = self.data.sort_values('timestamp').reset_index(drop=True)
        print(f"✅ 数据加载完成：{len(self.data)} 条 K 线")
        return self
    
    def run(self) -> BacktestResult:
        """运行回测"""
        if self.data is None or self.strategy is None:
            raise ValueError("请先加载数据和添加策略")
        
        print(f"🚀 开始回测...")
        self.equity_curve = [self.initial_cash]
        
        # 初始化策略
        self.strategy.on_init()
        
        # 遍历 K 线
        for i in range(len(self.data)):
            bar = self._get_bar(i)
            self.current_bar = i
            
            # 更新策略
            self.strategy.on_bar(bar)
            
            # 记录权益
            equity = self.broker.get_equity(bar.close)
            self.equity_curve.append(equity)
        
        # 计算绩效
        result = self._calculate_result()
        print(result.summary())
        return result
    
    def _get_bar(self, index: int) -> Bar:
        """获取 K 线"""
        row = self.data.iloc[index]
        return Bar(
            timestamp=row['timestamp'],
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row.get('volume', 0)
        )
    
    def _calculate_result(self) -> BacktestResult:
        """计算回测结果"""
        equity_array = np.array(self.equity_curve)
        
        # 总收益率
        total_return = (equity_array[-1] - self.initial_cash) / self.initial_cash * 100
        
        # 年化收益率 (假设 252 个交易日)
        days = len(equity_array)
        annual_return = ((equity_array[-1] / self.initial_cash) ** (252 / days) - 1) * 100 if days > 0 else 0
        
        # 夏普比率
        returns = np.diff(equity_array) / equity_array[:-1]
        sharpe_ratio = np.sqrt(252) * np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # 最大回撤
        peak = np.maximum.accumulate(equity_array)
        drawdown = (peak - equity_array) / peak * 100
        max_drawdown = np.max(drawdown)
        
        # 交易统计
        trades = self.broker.trades
        total_trades = len([t for t in trades if t.direction == 'SELL'])
        
        # 计算盈亏
        profits = []
        for i in range(0, len(trades) - 1):
            if trades[i].direction == 'BUY' and trades[i+1].direction == 'SELL':
                profit = (trades[i+1].price - trades[i].price) * trades[i].shares
                profits.append(profit)
        
        winning_trades = len([p for p in profits if p > 0])
        win_rate = winning_trades / len(profits) * 100 if profits else 0
        
        avg_profit = np.mean([p for p in profits if p > 0]) if any(p > 0 for p in profits) else 0
        avg_loss = abs(np.mean([p for p in profits if p < 0])) if any(p < 0 for p in profits) else 1
        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0
        
        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            total_trades=total_trades,
            winning_trades=winning_trades,
            equity_curve=self.equity_curve,
            trades=trades
        )
    
    def generate_report(self, output_path: str = 'reports/backtest_report.html'):
        """生成 HTML 报告"""
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        result = self._calculate_result()
        
        # 生成权益曲线数据
        equity_data = ""
        for i, eq in enumerate(self.equity_curve):
            equity_data += f"{{x: {i}, y: {eq:.2f}}},\n"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>回测报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; }}
        .metric-label {{ font-size: 0.9em; opacity: 0.9; }}
        .chart-container {{ margin: 30px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .buy {{ color: #e74c3c; }}
        .sell {{ color: #27ae60; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 股票策略回测报告</h1>
        <p>生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{result.total_return:.2f}%</div>
                <div class="metric-label">总收益率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.annual_return:.2f}%</div>
                <div class="metric-label">年化收益率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.sharpe_ratio:.2f}</div>
                <div class="metric-label">夏普比率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.max_drawdown:.2f}%</div>
                <div class="metric-label">最大回撤</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.win_rate:.2f}%</div>
                <div class="metric-label">胜率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.total_trades}</div>
                <div class="metric-label">交易次数</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>权益曲线</h2>
            <canvas id="equityChart"></canvas>
        </div>
        
        <h2>交易记录</h2>
        <table>
            <tr><th>时间</th><th>方向</th><th>价格</th><th>数量</th><th>手续费</th></tr>
            {''.join([f"<tr><td>{t.timestamp.strftime('%Y-%m-%d')}</td><td class='{t.direction.lower()}'>{t.direction}</td><td>{t.price:.2f}</td><td>{t.shares}</td><td>{t.commission:.2f}</td></tr>" for t in result.trades[:20]])}
        </table>
        {f'<p>共 {len(result.trades)} 条交易记录，显示前 20 条</p>' if len(result.trades) > 20 else ''}
    </div>
    
    <script>
        const ctx = document.getElementById('equityChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: Array.from({{length: {len(self.equity_curve)}}}, (_, i) => i),
                datasets: [{{
                    label: '账户权益',
                    data: [{','.join(map(str, self.equity_curve))}],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    fill: true,
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: true }}
                }},
                scales: {{
                    y: {{ beginAtZero: false }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📄 报告已生成：{output_path}")
        return output_path
