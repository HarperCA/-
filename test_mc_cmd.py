import sys
sys.path.insert(0, '.')

from core.console import configure_console_output
from agent.quant_agent import QuantAgent
from core.indicators import add_all_indicators

configure_console_output()

agent = QuantAgent(paper_trade=False)
symbol = "021662"
market = "fund"

print(f"\n🎲 正在对 {symbol} 执行蒙特卡洛模拟...")
df = agent.data_fetcher.fetch(symbol, market=market, period="1y")
print(f"   获取到 {len(df)} 天数据")

equity = (df["close"] / df["close"].iloc[0])
mc = agent.backtest_engine.monte_carlo(equity, n_simulations=10000, n_days=252)

print(f"\n{'='*60}")
print(f"🎲 {symbol} 蒙特卡洛模拟报告")
print(f"{'='*60}")
print(f"  历史数据: {len(df)} 天")
print(f"  模拟次数: {mc['n_simulations']:,} 次")
print(f"  模拟周期: {mc['n_days']} 个交易日")
print(f"\n📈 收益分布:")
print(f"  胜率: {mc['win_rate']*100:.1f}%")
print(f"  平均收益: {mc['mean_return']*100:.2f}%")
print(f"  中位数收益: {mc['median_return']*100:.2f}%")
print(f"  最好5%: {mc['p95_return']*100:.2f}%")
print(f"  最差5%: {mc['p5_return']*100:.2f}%")
print(f"\n⚠️ 回撤分布:")
print(f"  平均最大回撤: {mc['mean_max_dd']*100:.2f}%")
print(f"  最差5%回撤: {mc['p5_max_dd']*100:.2f}%")
print(f"  回撤超20%概率: {mc['prob_20pct_dd']*100:.1f}%")
print(f"  回撤超30%概率: {mc['prob_30pct_dd']*100:.1f}%")
print(f"{'='*60}")
